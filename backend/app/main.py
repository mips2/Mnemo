# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from .database import create_db_and_tables, get_session
from .models import User, Feedback
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from .memory import MemoryStore
from .active_learning import ActiveLearner

from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from datetime import timedelta

# Initialize FastAPI app
app = FastAPI(title="Dynamic Memory Transformer with Active Learning")

# CORS Configuration
origins = [
    "http://localhost:3000",  # React frontend
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Initialize model and tokenizer globally to avoid reloading
MODEL_NAME = "distilgpt2"  # Replace with LLaMA or desired model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

active_learner = ActiveLearner(model, tokenizer)

# Pydantic models for requests
class UserCreate(BaseModel):
    email: str
    password: str

class FeedbackData(BaseModel):
    user_input: str
    model_response: str
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
@app.post("/login", summary="Login and get access token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Generate Response Endpoint
@app.post("/generate", summary="Generate response from the model")
@limiter.limit("10/minute")
def generate(query: FeedbackData, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        memory_store = MemoryStore(session, current_user)
        memory = memory_store.retrieve_memory(query.user_input)
        memory_context = " ".join(memory)
        augmented_input = f"Context: {memory_context}\nUser: {query.user_input}\nAssistant:"

        inputs = tokenizer.encode(augmented_input, return_tensors='pt')
        outputs = model.generate(
            inputs,
            max_length=150,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        assistant_reply = response.split("Assistant:")[-1].strip()

        # Update memory
        memory_store.add_to_memory(query.user_input)
        memory_store.add_to_memory(assistant_reply)

        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Feedback Endpoint
@app.post("/feedback", summary="Provide feedback to improve the model")
@limiter.limit("5/minute")
def feedback(feedback_data: FeedbackData, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        memory_store = MemoryStore(session, current_user)
        combined_input = f"Context: {' '.join(memory_store.retrieve_memory(feedback_data.user_input))}\nUser: {feedback_data.user_input}\nAssistant:"

        inputs = tokenizer.encode(combined_input, return_tensors='pt')
        uncertainty = active_learner.measure_uncertainty(inputs)

        threshold = 1.0  # Adjust based on experimentation
        if uncertainty > threshold:
            corrected_response = feedback_data.corrected_response
            input_ids = tokenizer.encode(combined_input, return_tensors='pt')
            labels = tokenizer.encode(f"Assistant: {corrected_response}", return_tensors='pt')

            loss = active_learner.fine_tune(input_ids, labels)

            # Store feedback
            feedback_entry = Feedback(
                user_id=current_user.id,
                user_input=feedback_data.user_input,
                model_response=feedback_data.model_response,
                corrected_response=corrected_response
            )
            session.add(feedback_entry)
            session.commit()

            return {"status": "Model fine-tuned", "loss": loss}
        else:
            return {"status": "No fine-tuning needed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
