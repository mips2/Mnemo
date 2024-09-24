from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str
    memories: List["Memory"] = Relationship(back_populates="user")
    feedbacks: List["Feedback"] = Relationship(back_populates="user")

class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    content: str
    user: Optional[User] = Relationship(back_populates="memories")

class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_input: str
    ai_response: str  # Changed from model_reply to ai_response
    corrected_response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates="feedbacks")

class ChatHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_input: str
    ai_response: str  # Changed from model_response to ai_response
    timestamp: datetime = Field(default_factory=datetime.utcnow)
