from pydantic import BaseModel
from typing import Dict, List, Optional, Literal
from datetime import datetime


class ReactionData(BaseModel):
    """Represents reactions on a message with emoji to usernames mapping"""
    emoji: Dict[str, List[str]] = {}  # {emoji: [usernames]}


class Message(BaseModel):
    """Base message model with reactions support"""
    id: str
    type: Literal["message", "join", "leave", "reaction", "add_reaction", "remove_reaction"]
    user: str
    content: Optional[str] = None
    timestamp: datetime
    reactions: ReactionData = ReactionData()
    online: Optional[List[str]] = None  # For join/leave messages


class MessageBroadcast(BaseModel):
    """Model for messages sent to WebSocket clients"""
    type: Literal["message", "join", "leave", "reaction", "reaction_update", "add_reaction", "remove_reaction"]
    user: str
    content: Optional[str] = None
    message_id: Optional[str] = None  # For reaction updates
    reactions: Optional[ReactionData] = None
    emoji: Optional[str] = None  # For reaction updates
    users: Optional[List[str]] = None  # For reaction updates
    online: Optional[List[str]] = None
    timestamp: Optional[datetime] = None


class ReactionRequest(BaseModel):
    """Model for incoming reaction requests"""
    type: Literal["reaction"]
    message_id: str
    emoji: str
    action: Literal["add", "remove"]


class AddReactionRequest(BaseModel):
    """Model for incoming add_reaction requests"""
    type: Literal["add_reaction"]
    message_id: str
    emoji: str


class RemoveReactionRequest(BaseModel):
    """Model for incoming remove_reaction requests"""
    type: Literal["remove_reaction"]
    message_id: str
    emoji: str


class MessageRequest(BaseModel):
    """Model for incoming message requests"""
    type: Literal["message"]
    content: str
