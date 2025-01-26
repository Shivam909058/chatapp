# recieve the message from the client

import random
from fastapi import WebSocket, FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi import WebSocketDisconnect
import json
from datetime import datetime
import uuid
from fastapi.templating import Jinja2Templates
from database import Database
from supabase_client import test_connection
import aiofiles
import os
from uuid import uuid4
from fastapi.staticfiles import StaticFiles
import shutil 
from pathlib import Path
from fastapi.security import HTTPBearer
from security import validate_password_strength, generate_room_id
import rate_limit
import magic  # for file type verification
from repeat_every import repeat_every

app = FastAPI()
templates = Jinja2Templates(directory="templates")

client_id = random.randint(0, 1000)
print(client_id)

# Add this before starting the app
if not test_connection():
    raise Exception("Failed to connect to Supabase. Please check your credentials.")

# User and room management
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_details: dict[str, dict] = {}
        self.rooms: dict[str, list[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_details:
            # Remove user from room
            room_id = self.user_details[user_id].get('room_id')
            if room_id and room_id in self.rooms:
                self.rooms[room_id].remove(user_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            del self.user_details[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.rooms:
            for user_id in self.rooms[room_id]:
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

security = HTTPBearer()
ALLOWED_FILE_TYPES = {
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Add rate limiting
limiter = rate_limit.RateLimiter(requests=100, window=60)  # 100 requests per minute

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/join")
async def join_chat(request: Request, name: str = Form(...), room_id: str = Form(...)):
    # Check if name is already in use in the room
    for user in manager.user_details.values():
        if user['name'] == name and user['room_id'] == room_id:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Name is already in use in this room"
            })
    
    user_id = str(uuid.uuid4())
    manager.user_details[user_id] = {
        "name": name,
        "room_id": room_id,
        "user_id": user_id
    }
    if room_id not in manager.rooms:
        manager.rooms[room_id] = []
    manager.rooms[room_id].append(user_id)
    return RedirectResponse(f"/chat/{user_id}", status_code=303)

@app.get("/chat/{user_id}")
async def chat(request: Request, user_id: str):
    if user_id not in manager.user_details:
        return RedirectResponse("/")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user_id": user_id,
        "user_name": manager.user_details[user_id]['name'],
        "room_id": manager.user_details[user_id]['room_id']
    })

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    if user_id not in manager.user_details:
        await websocket.close()
        return

    user_data = manager.user_details[user_id]
    await manager.connect(websocket, user_id)
    
    try:
        # Load previous messages
        messages = Database.get_messages(user_data['room_id'])
        for msg in messages.data:
            await websocket.send_text(json.dumps({
                "type": "message",
                "message": msg['message'],
                "sender": msg['sender_id'],
                "sender_name": msg['sender_name'],
                "time": msg['created_at']
            }))
        
        # Send user list
        room_users = [
            {"id": uid, "name": manager.user_details[uid]['name']}
            for uid in manager.rooms[user_data['room_id']]
        ]
        await manager.broadcast_to_room(json.dumps({
            "type": "user_list",
            "users": room_users
        }), user_data['room_id'])
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Add timestamp to all messages
            message_data['time'] = datetime.now().strftime("%H:%M")
            
            if message_data.get('type') == 'file':
                # Broadcast file message to all users in the room
                await manager.broadcast_to_room(json.dumps({
                    "type": "file",
                    "fileUrl": message_data['fileUrl'],
                    "fileName": message_data['fileName'],
                    "fileType": message_data['fileType'],
                    "fileSize": message_data['fileSize'],
                    "sender": user_id,
                    "sender_name": manager.user_details[user_id]['name'],
                    "time": message_data['time']
                }), user_data['room_id'])
            else:
                # Handle regular text messages
                await manager.broadcast_to_room(json.dumps(message_data), 
                    user_data['room_id'])
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        Database.delete_user(user_id)
        await manager.broadcast_to_room(json.dumps({
            "type": "message",
            "message": f"{user_data['name']} has left the chat",
            "sender": "system",
            "sender_name": "System",
            "time": datetime.now().strftime("%H:%M")
        }), user_data['room_id'])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount the uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/upload")
@limiter.limit()
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check file size
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Verify file type
        content_type = magic.from_buffer(await file.read(1024), mime=True)
        await file.seek(0)
        
        if content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_extension}"
        file_location = UPLOAD_DIR / unique_filename
        
        with file_location.open("wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        # Get file size
        file_size = file_location.stat().st_size
        size_str = get_file_size_str(file_size)
        
        return JSONResponse({
            "url": f"/uploads/{unique_filename}",
            "filename": file.filename,
            "size": size_str,
            "type": file.content_type
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_file_size_str(size_in_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} GB"

@app.post("/create-room")
@limiter.limit()
async def create_room(
    request: Request,
    name: str = Form(...),
    password: str = Form(...)
):
    # Validate password strength
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Generate secure room ID
    room_id = generate_room_id()
    
    # Create room in database
    room = Database.create_room(room_id, password, name)
    if not room:
        raise HTTPException(status_code=500, detail="Failed to create room")
    
    return {"room_id": room_id}

# Add cleanup task
@app.on_event("startup")
@repeat_every(hours=24)
async def cleanup_inactive_rooms():
    Database.cleanup_inactive_rooms()

