import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import json
import bcrypt
from datetime import datetime
import asyncio

app = FastAPI()

# File lưu trữ dữ liệu (sẽ thay bằng database trong tương lai)
DATA_FILE = "chat_data.json"

# Route mặc định để kiểm tra server
@app.get("/")
async def root():
    return {"message": "Niltalk Server is running! Access /docs for API documentation."}

# Khởi tạo dữ liệu
def init_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": {}, "messages": {}}
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

# Đọc dữ liệu
def read_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        init_data()
        return {"users": {}, "messages": {}}

# Ghi dữ liệu
def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Quản lý các client WebSocket
connected_clients = {}  # Lưu các client theo username: websocket

@app.post("/register")
async def register(username: str, password: str):
    data = read_data()
    if username in data["users"]:
        return JSONResponse({"error": "Tên tài khoản đã tồn tại"}, status_code=400)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    data["users"][username] = hashed.decode()
    data["messages"][username] = []
    write_data(data)
    return {"message": "Đăng ký thành công"}

@app.post("/login")
async def login(username: str, password: str):
    data = read_data()
    if username in data["users"] and bcrypt.checkpw(password.encode(), data["users"][username].encode()):
        return {"message": "Đăng nhập thành công"}
    return JSONResponse({"error": "Tên tài khoản hoặc mật khẩu sai"}, status_code=400)

@app.get("/users")
async def get_users():
    data = read_data()
    return {"users": [user for user in data["users"]]}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connected_clients[username] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            saved_data = read_data()
            saved_data["messages"][data["receiver"]].append(data)
            saved_data["messages"][username].append(data)
            write_data(saved_data)
            # Gửi tin nhắn đến người nhận nếu họ online
            receiver_ws = connected_clients.get(data["receiver"])
            if receiver_ws:
                await receiver_ws.send_json(data)
            # Gửi lại cho người gửi để cập nhật giao diện
            await websocket.send_json(data)
    except WebSocketDisconnect:
        del connected_clients[username]
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if username in connected_clients:
            del connected_clients[username]

if __name__ == "__main__":
    import uvicorn
    init_data()
    uvicorn.run(app, host="0.0.0.0", port=8001)