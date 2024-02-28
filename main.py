from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict
import uuid

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

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_identifiers: Dict[WebSocket, str] = {}
        self.display_names: Dict[str, str] = {}
        self.click_counts: Dict[str, int] = {}  # 클릭 카운트를 저장하는 사전
        self.available_numbers = set()
        self.next_guest_number = 1

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        unique_id = str(uuid.uuid4())
        if self.available_numbers:
            display_number = min(self.available_numbers)
            self.available_numbers.remove(display_number)
        else:
            display_number = self.next_guest_number
            self.next_guest_number += 1
        display_name = f"guest{display_number}"
        self.user_identifiers[websocket] = unique_id
        self.display_names[unique_id] = display_name
        self.click_counts[unique_id] = 0  # 초기 클릭 카운트는 0
        await self.broadcast_users()

    async def disconnect(self, websocket: WebSocket):
        unique_id = self.user_identifiers.pop(websocket, None)
        if unique_id:
            display_name = self.display_names.pop(unique_id, None)
            self.click_counts.pop(unique_id, None)  # 클릭 카운트 정보도 제거
            self.active_connections.remove(websocket)
            if display_name:
                number = int(display_name.replace("guest", ""))
                self.available_numbers.add(number)
            await self.broadcast_users()

    async def broadcast_users(self):
        users_list = [{"name": name, "clicks": self.click_counts[uid]} for uid, name in self.display_names.items()]
        for connection in self.active_connections:
            await connection.send_json({"users": users_list})

    async def update_click_count(self, unique_id: str):
        if unique_id in self.click_counts:
            self.click_counts[unique_id] += 1
            await self.broadcast_users()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "click":
                unique_id = manager.user_identifiers[websocket]
                await manager.update_click_count(unique_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

manager = ConnectionManager()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4001)