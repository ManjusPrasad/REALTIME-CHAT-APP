from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
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


from .auth import router as auth_router, verify_token

app = FastAPI()
app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...), view_once: bool = Form(False)):
    """Save uploaded file and optionally create a view-once token.
    If `view_once` is True a token URL `/view/{token}` is returned; otherwise a static `/uploads/{filename}` URL is returned.
    """
    # Verify Authorization header (expect Bearer token)
    auth = request.headers.get('authorization')
    if not auth or not auth.lower().startswith('bearer '):
        return HTMLResponse(status_code=401, content="Unauthorized")
    token = auth.split(None, 1)[1]
    try:
        verify_token(token)
    except Exception:
        return HTMLResponse(status_code=401, content="Unauthorized")

    # Save uploaded file to uploads dir (use absolute path to avoid relative-path issues)
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    # make filename unique to avoid collisions
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if view_once:
        token = uuid.uuid4().hex
        # store absolute normalized path
        manager.view_tokens[token] = os.path.abspath(file_path)
        url = f"/view/{token}"
        return {"url": url, "token": token}
    else:
        # Return the URL to access the file
        url = f"/uploads/{unique_name}"
        return {"url": url}


@app.get("/view/{token}")
async def view_once(token: str):
    """Serve a view-once file for the given token and delete it after first successful fetch.
    Returns 404 if token not found or already consumed.
    """
    token_map = manager.view_tokens
    if token not in token_map:
        return HTMLResponse(status_code=404, content="Not found")

    file_path = token_map[token]
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        # cleanup and 404
        token_map.pop(token, None)
        return HTMLResponse(status_code=404, content="Not found")

    # Serve the file as FileResponse then delete it and remove the token
    try:
        response = FileResponse(path=file_path)
        # remove token and file after serving
        try:
            os.remove(file_path)
        except Exception:
            pass
        token_map.pop(token, None)
        return response
    except Exception:
        return HTMLResponse(status_code=500, content="Error serving file")
templates = Jinja2Templates(directory="templates")


@app.get("/privacy")
async def privacy_page():
        """Serve the `PRIVACY.md` file as simple readable HTML."""
        md_path = os.path.join(os.path.dirname(__file__), '..', 'PRIVACY.md')
        try:
                with open(md_path, 'r', encoding='utf-8') as f:
                        md = f.read()
        except Exception:
                return HTMLResponse('<p>Privacy file not found.</p>', status_code=404)

        # Minimal safe rendering: escape HTML and preserve line breaks
        safe = md.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html = f"""
        <html>
            <head>
                <meta charset='utf-8'>
                <title>Privacy</title>
                <style>body{{font-family:Segoe UI,Arial,Helvetica,sans-serif;padding:20px;max-width:900px;margin:auto}} pre{{white-space:pre-wrap}}</style>
            </head>
            <body>
                <h1>Privacy</h1>
                <pre>{safe}</pre>
            </body>
        </html>
        """
        return HTMLResponse(html)

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}
        self.users: Dict[str, Dict[str, str]] = {}   # room  {ws_id: username}
        self.messages: Dict[str, Dict[str, Message]] = {}  # room  {message_id: Message}
        # map view tokens to file paths for view-once media
        self.view_tokens: Dict[str, str] = {}

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


@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.websocket("/ws/{room}/{username}")
async def websocket_endpoint(websocket: WebSocket, room: str, username: str):
    # Extract token from query params and verify
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=1008)
        return
    try:
        token_user = verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return
    # Ensure the token user matches the username path
    if token_user != username:
        await websocket.close(code=1008)
        return

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
                        view_once=getattr(message_request, "view_once", False),
                        timestamp=datetime.now(),
                    )
                    manager.store_message(room, message)
                    await manager.broadcast(room, MessageBroadcast(
                        type="message",
                        user=username,
                        content=message_request.content,
                        view_once=getattr(message_request, "view_once", False),
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