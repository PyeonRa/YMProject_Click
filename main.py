from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import uvicorn
from typing import List, Dict
import uuid
import json


app = FastAPI()

app.mount("/static", StaticFiles(directory="FRONT/public"), name="static")
templates = Jinja2Templates(directory="FRONT/public")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 접속을 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient("mongodb+srv://pyeonra315:maple315@jabclick.wahtzrv.mongodb.net/")
    app.mongodb = app.mongodb_client.jabcat

@app.on_event("shutdown")
async def shutdown_db_c3lient():
    app.mongodb_client.close()


class UserInfo(BaseModel):
    nickName: str
    uuid: str
    click: int = 0

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_identifiers: Dict[WebSocket, str] = {}
        self.available_guest_numbers: List[int] = []

    async def connect(self, websocket: WebSocket, provided_uuid: str = None):
        is_new_user = False
        unique_id = provided_uuid or str(uuid.uuid4())

        if provided_uuid:
            existing_user = await app.mongodb["users"].find_one({"uuid": provided_uuid})
            if existing_user:
                await app.mongodb["users"].find_one_and_update(
                    {"uuid": unique_id},
                    {"$set": {"online": True}},
                    return_document=True
                )
            else:
                is_new_user = True
        else:
            is_new_user = True

        if is_new_user:
            if self.available_guest_numbers:
                next_guest_number = min(self.available_guest_numbers)
                self.available_guest_numbers.remove(next_guest_number)
            else:
                guest_users = await app.mongodb["users"].find({"nickName": {"$regex": "^guest"}}).to_list(length=None)
                guest_numbers = [int(user['nickName'][5:]) for user in guest_users if user['nickName'][5:].isdigit()]
                next_guest_number = max(guest_numbers) + 1 if guest_numbers else 1
            nickName = f"guest{next_guest_number}"

            await app.mongodb["users"].insert_one({
                "uuid": unique_id,
                "nickName": nickName,
                "click": 0,
                "online": True
            })
        else:
            nickName = existing_user['nickName']

        self.active_connections.append(websocket)
        self.user_identifiers[websocket] = unique_id

        return unique_id

    async def disconnect(self, websocket: WebSocket):
        unique_id = self.user_identifiers.get(websocket)
        if unique_id:
            self.active_connections.remove(websocket)
            del self.user_identifiers[websocket]

            user_info = await app.mongodb["users"].find_one({"uuid": unique_id})
            user_nickname = user_info["nickName"]

            if user_info:
                if user_nickname.startswith("guest"):
                    print(f"User {user_nickname} (uuid : {unique_id}) has disconnected")
                    guest_number = int(user_nickname[5:])
                    self.available_guest_numbers.append(guest_number)
                    self.available_guest_numbers.sort()


                    await app.mongodb["users"].delete_one({"uuid": unique_id})
                else:
                    print(f"User {user_nickname} (uuid : {unique_id}) has disconnected")

                    await app.mongodb["users"].update_one(
                        {"uuid": unique_id},
                        {"$set": {"online": False}}
                    )
                

                await self.broadcast_users()

    async def broadcast_users(self):
        users_cursor = app.mongodb["users"].find({"online": True})
        users_list = await users_cursor.to_list(length=None)
        users_info = [{
            "uuid": user["uuid"],
            "nickName": user.get("nickName", "Unknown"),
            "click": user.get("click", 0)
        } for user in users_list if user.get("online")]

        for connection in self.active_connections:
            await connection.send_json({"type": "users", "users": users_info})

    async def broadcast_ranking(self):
        non_guest_users_cursor = app.mongodb["users"].find({
            "nickName": {"$not": {"$regex": "^guest"}}
        }).sort("click", -1)

        non_guest_users = await non_guest_users_cursor.to_list(length=None)

        users_info = [{
            "nickName": user.get("nickName", "Unknown"),
            "click": user.get("click", 0)
        } for user in non_guest_users]

        for connection in self.active_connections:
            await connection.send_json({"type": "ranking", "users": users_info})

    async def update_click_count(self, unique_id: str):
        try:
            updated_user = await app.mongodb["users"].find_one_and_update(
                {"uuid": unique_id},
                {"$inc": {"click": 1}},
                return_document=True
            )

            if not updated_user:
                print(f"UUID: {unique_id}에 해당하는 사용자를 찾을 수 없습니다.")
                return False

            await self.broadcast_users()
            await self.broadcast_ranking()
            return True
        except Exception as e:
            print(f"UUID: {unique_id} 클릭 수 업데이트 중 오류 발생: {e}")
            return False

    async def store_info(self, user_info: UserInfo):
        unique_id = user_info['uuid']
        nickName = user_info['nickName']
        await app.mongodb["users"].find_one_and_update(
            {"uuid": unique_id},
            {"$set": {"nickName": nickName}},
            return_document=True
        )
        await self.broadcast_users()
        await self.broadcast_ranking()

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    provided_uuid = None

    initial_data = await websocket.receive_text()
    initial_json_data = json.loads(initial_data)
    provided_uuid = initial_json_data.get("uuid")
    
    unique_id = await manager.connect(websocket, provided_uuid)

    user_address = json.loads(await websocket.receive_text()).get("address")
    print(f"The connected user's address is : {user_address}")

    await websocket.send_json({"type": "welcome", "unique_id": unique_id, "message": "Welcome!"})
    await manager.broadcast_users()
    await manager.broadcast_ranking()


    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            if json_data["type"] == "click":
                await manager.update_click_count(unique_id)
            elif json_data["type"] == "nickname":
                nickname = json_data['nickname']
                store = UserInfo(nickName=nickname, uuid=unique_id)
                await manager.store_info(store.dict())

    except WebSocketDisconnect:
        await manager.disconnect(websocket)



@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=4001)