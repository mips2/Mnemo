from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
import torch
from pydantic import BaseModel

from .database import create_db_and_tables, get_session
from .models import User, Feedback, ChatHistory
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from .memory import MemoryStore
from .ai_model import generate_response, fine_tune_model

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Pydantic models for requests
class UserCreate(BaseModel):
    email: str
    password: str

class FeedbackData(BaseModel):
    user_input: str
    ai_response: str
    corrected_response: str

# User Registration
@app.post("/register", summary="Register a new user")
def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"msg": "User created successfully"}

# User Login
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Generate Response Endpoint
@app.post("/generate", summary="Generate response from the model")
@limiter.limit("10/minute")
def generate(request: Request, query: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        user_input = query.get("user_input")
        if not user_input:
            raise HTTPException(status_code=400, detail="User input is required")

        memory_store = MemoryStore(session, current_user)
        ai_response = generate_response(user_input, memory_store, current_user, session)

        # Save chat history
        chat_history = ChatHistory(user_id=current_user.id, user_input=user_input, ai_response=ai_response)
        session.add(chat_history)
        session.commit()

        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat History Endpoint
@app.get("/chat-history")
async def get_chat_history(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    statement = select(ChatHistory).where(ChatHistory.user_id == current_user.id).order_by(ChatHistory.timestamp)
    chat_history = session.exec(statement).all()
    return chat_history

# Feedback Endpoint
@app.post("/feedback")
async def submit_feedback(feedback_data: FeedbackData, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    feedback = Feedback(
        user_id=current_user.id,
        user_input=feedback_data.user_input,
        ai_response=feedback_data.ai_response,
        corrected_response=feedback_data.corrected_response
    )
    session.add(feedback)
    session.commit()
    
    # Fine-tune the model
    loss = fine_tune_model(feedback_data.user_input, feedback_data.corrected_response)
    
    return {"message": "Feedback submitted and model fine-tuned successfully", "loss": loss}
