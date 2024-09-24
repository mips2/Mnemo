from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

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
    model_reply: str  # Changed from model_response to model_reply
    corrected_response: str
    user: Optional[User] = Relationship(back_populates="feedbacks")
