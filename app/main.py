from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Union, Optional
from starlette.requests import Request
from datetime import datetime
import uvicorn, json, uuid
from pydantic import ValidationError
from .schemas import Message, MessageBroadcast, ReactionRequest, MessageRequest, ReactionData, AddReactionRequest, RemoveReactionRequest


from fastapi import UploadFile, File, Form
import os, shutil

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save uploaded file to uploads dir
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Return the URL to access the file
    url = f"/uploads/{file.filename}"
    return {"url": url}
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}
        self.users: Dict[str, Dict[str, str]] = {}   # room  {ws_id: username}
        self.messages: Dict[str, Dict[str, Message]] = {}  # room  {message_id: Message}

    async def connect(self, room: str, username: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)
        self.users.setdefault(room, {})[id(websocket)] = username
        await self.broadcast(room, {"type": "join", "user": username, "online": list(self.users[room].values())})

    async def disconnect(self, room: str, websocket: WebSocket):
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
            if room in self.users and id(websocket) in self.users[room]:
                username = self.users[room].pop(id(websocket))
                await self.broadcast(room, {"type": "leave", "user": username, "online": list(self.users[room].values())})
            if not self.rooms[room]:
                del self.rooms[room]
                if room in self.users:
                    del self.users[room]

    def store_message(self, room: str, message: Message) -> None:
        """Store a message in the room''s message history"""
        self.messages.setdefault(room, {})[message.id] = message
    
    def get_message(self, room: str, message_id: str) -> Optional[Message]:
        """Get a specific message by ID"""
        return self.messages.get(room, {}).get(message_id)
    
    def verify_user_in_room(self, room: str, username: str) -> bool:
        """Verify that a user is currently connected to the room"""
        if room not in self.users:
            return False
        return username in self.users[room].values()
    
    def add_reaction(self, room: str, message_id: str, emoji: str, username: str) -> bool:
        """Add a reaction to a message. Returns True if successful."""
        message = self.get_message(room, message_id)
        if not message:
            return False
        
        if emoji not in message.reactions.emoji:
            message.reactions.emoji[emoji] = []
        
        if username not in message.reactions.emoji[emoji]:
            message.reactions.emoji[emoji].append(username)
        
        return True
    
    def remove_reaction(self, room: str, message_id: str, emoji: str, username: str) -> bool:
        """Remove a reaction from a message. Returns True if successful."""
        message = self.get_message(room, message_id)
        if not message:
            return False
        
        if emoji in message.reactions.emoji and username in message.reactions.emoji[emoji]:
            message.reactions.emoji[emoji].remove(username)
            # Remove emoji key if no users have this reaction
            if not message.reactions.emoji[emoji]:
                del message.reactions.emoji[emoji]
            return True
        
        return False

    async def broadcast(self, room: str, message: Union[dict, MessageBroadcast]):
        """Broadcast a message to all clients in a room"""
        if room in self.rooms:
            # Convert to dict if it''s a Pydantic model
            if isinstance(message, MessageBroadcast):
                message_data = message.model_dump(exclude_none=True)
                # Convert datetime to ISO string for JSON serialization
                if "timestamp" in message_data and message_data["timestamp"]:
                    message_data["timestamp"] = message_data["timestamp"].isoformat()
                # Convert reactions to dict format
                if "reactions" in message_data and message_data["reactions"]:
                    message_data["reactions"] = message_data["reactions"]["emoji"]
            else:
                message_data = message
            
            message_text = json.dumps(message_data)
            disconnected = []
            for websocket in self.rooms[room]:
                try:
                    await websocket.send_text(message_text)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                await self.disconnect(room, websocket)

manager = ConnectionManager()

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{room}/{username}")
async def websocket_endpoint(websocket: WebSocket, room: str, username: str):
    await manager.connect(room, username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            try:
                if data["type"] == "message":
                    message_request = MessageRequest(**data)
                    message = Message(
                        id=str(uuid.uuid4()),
                        type="message",
                        user=username,
                        content=message_request.content,
                        timestamp=datetime.now(),
                    )
                    manager.store_message(room, message)
                    await manager.broadcast(room, MessageBroadcast(
                        type="message",
                        user=username,
                        content=message_request.content,
                        message_id=message.id,
                        timestamp=message.timestamp
                    ))
                elif data["type"] == "add_reaction":
                    request = AddReactionRequest(**data)
                    if manager.verify_user_in_room(room, username):
                        if manager.add_reaction(room, request.message_id, request.emoji, username):
                            message = manager.get_message(room, request.message_id)
                            if message:
                                await manager.broadcast(room, MessageBroadcast(
                                    type="reaction_update",
                                    message_id=request.message_id,
                                    emoji=request.emoji,
                                    users=message.reactions.emoji[request.emoji]
                                ))
                elif data["type"] == "remove_reaction":
                    request = RemoveReactionRequest(**data)
                    if manager.verify_user_in_room(room, username):
                        if manager.remove_reaction(room, request.message_id, request.emoji, username):
                            message = manager.get_message(room, request.message_id)
                            users = message.reactions.emoji.get(request.emoji, []) if message else []
                            await manager.broadcast(room, MessageBroadcast(
                                type="reaction_update",
                                message_id=request.message_id,
                                emoji=request.emoji,
                                users=users
                            ))
            except ValidationError as e:
                print(f"Validation error: {e}")
                        
    except WebSocketDisconnect:
        await manager.disconnect(room, websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)