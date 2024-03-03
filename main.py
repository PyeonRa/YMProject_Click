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
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.mongodb = app.mongodb_client.click_game

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


class UserInfo(BaseModel):
    nickName: str
    click: int
    uuid: str


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_identifiers: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, provided_uuid: str = None):
        if provided_uuid:
            existing_user = await app.mongodb["users"].find_one({"uuid": provided_uuid})
            if existing_user:
                await app.mongodb["users"].update_one(
                    {"uuid": provided_uuid},
                    {"$set": {"online": True}}
                )
                unique_id = provided_uuid
            else:
                unique_id = str(uuid.uuid4())
                display_name = f"guest{len(self.active_connections) + 1}"
                await app.mongodb["users"].insert_one({
                    "uuid": unique_id,
                    "nickName": display_name,
                    "click": 0,
                    "online": True
                })
        else:
            unique_id = str(uuid.uuid4())
            display_name = f"guest{len(self.active_connections) + 1}"
            await app.mongodb["users"].insert_one({
                "uuid": unique_id,
                "nickName": display_name,
                "click": 0,
                "online": True
            })
    
        self.active_connections.append(websocket)
        self.user_identifiers[websocket] = unique_id
        await websocket.send_json({"type": "welcome", "unique_id": unique_id, "message": f"Welcome, your ID is {unique_id}"})
        await self.broadcast_users()

    async def disconnect(self, websocket: WebSocket):
        unique_id = self.user_identifiers.get(websocket)
        if unique_id:
            self.active_connections.remove(websocket)
            del self.user_identifiers[websocket]

            user_info = await app.mongodb["users"].find_one({"uuid": unique_id})

            if user_info:
                if user_info["nickName"].startswith("guest"):
                    await app.mongodb["users"].delete_one({"uuid": unique_id})
                else:
                    await app.mongodb["users"].update_one(
                        {"uuid": unique_id},
                        {"$set": {"online": False}}
                    )
                print(f"User {unique_id} disconnected")

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


    async def update_click_count(self, unique_id: str):
        await app.mongodb["users"].update_one({"uuid": unique_id}, {"$inc": {"click": 1}})
        await self.broadcast_users()

    async def click_count(self, unique_id: str):
        user_info = await app.mongodb["users"].find_one({"uuid": unique_id})
        if user_info:
            return user_info.get("click", 0)
        return 0

    async def store_info(self, user_info: UserInfo):
        await app.mongodb["users"].insert_one(user_info)

    async def get_info(self, unique_id: str):
        info = await app.mongodb["users"].find_one({"uuid": unique_id})
        if info:
            return info
        else:
            print(f"No information found for UUID: {unique_id}")
            return None


manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    data = await websocket.receive_text()
    json_data = json.loads(data)
    provided_uuid = json_data.get("uuid")

    await manager.connect(websocket, provided_uuid)
    try:
        unique_id = manager.user_identifiers[websocket]
        while True:
            if json_data["type"] == "click":
                await manager.update_click_count(unique_id)
            elif json_data["type"] == "nickname":
                clicked = await manager.click_count(unique_id)
                nickname = json_data['nickname']
                store = UserInfo(nickName=nickname, click=clicked, uuid=unique_id)
                await manager.store_info(store.dict())
                await manager.get_info(unique_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)



@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=4001)