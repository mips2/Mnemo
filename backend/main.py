# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from models import User, Memory, Feedback
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from memory import MemoryStore
from active_learning import ActiveLearner

# Constants for JWT
SECRET_KEY = "your_secret_key_here"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI
app = FastAPI(title="Dynamic Memory Transformer with Active Learning")

# Create tables
models.Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
    
def get_password_hash(password):
    return pwd_context.hash(password)

# JWT token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Query(BaseModel):
    text: str

class FeedbackData(BaseModel):
    user_input: str
    model_response: str
    feedback: str  # Corrected response from the user

# OAuth2 dependency
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Authenticate user
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Initialize transformer components
MODEL_NAME = "distilgpt2"  # Use a small transformer model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

memory_store = MemoryStore()
active_learner = ActiveLearner(MODEL_NAME, tokenizer, model)

# Routes

@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/generate")
def generate(query: Query, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Retrieve relevant memory from the database
        user_memories = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.timestamp.desc()).limit(5).all()
        memory_texts = [mem.text for mem in user_memories]
        memory_context = " ".join(memory_texts)
        
        # Combine user input with memory context
        augmented_input = f"Context: {memory_context}\nUser: {query.text}\nAssistant:"
        
        # Tokenize and generate response
        inputs = tokenizer.encode(augmented_input, return_tensors='pt')
        outputs = model.generate(inputs, max_length=150, pad_token_id=tokenizer.eos_token_id, 
                                 do_sample=True, top_p=0.95, top_k=60)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the assistant's reply
        assistant_reply = response.split("Assistant:")[-1].strip()
        
        # Update memory with the latest interaction
        new_memory_user = Memory(user_id=current_user.id, text=query.text)
        new_memory_assistant = Memory(user_id=current_user.id, text=assistant_reply)
        db.add(new_memory_user)
        db.add(new_memory_assistant)
        db.commit()
        
        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def feedback(feedback_data: FeedbackData, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Measure uncertainty
        user_memories = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.timestamp.desc()).limit(5).all()
        memory_texts = [mem.text for mem in user_memories]
        memory_context = " ".join(memory_texts)
        
        combined_input = f"Context: {memory_context}\nUser: {feedback_data.user_input}\nAssistant:"
        inputs = tokenizer.encode(combined_input, return_tensors='pt')
        uncertainty = active_learner.measure_uncertainty(inputs)
        
        threshold = 1.0  # Define your own threshold based on experimentation
        if uncertainty > threshold:
            # Fine-tune the model with user feedback
            corrected_response = feedback_data.feedback
            labels = tokenizer.encode(f"Assistant: {corrected_response}", return_tensors='pt')
            loss = active_learner.fine_tune(inputs, labels)
            
            # Save feedback to the database
            new_feedback = Feedback(
                user_id=current_user.id,
                user_input=feedback_data.user_input,
                model_response=feedback_data.model_response,
                feedback_text=feedback_data.feedback
            )
            db.add(new_feedback)
            db.commit()
            
            return {"status": "Model fine-tuned", "loss": loss}
        else:
            return {"status": "No fine-tuning needed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
