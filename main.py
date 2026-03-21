from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import engine, get_db
from ai.ghost_assistant import generate_work_order

app = FastAPI(title="SkillGrid Backend API")

# --- Run DB creation on startup (IMPORTANT FIX) ---
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", 
        "https://marketplace-54ezlwksp-aakarsh151-cpus-projects.vercel.app/"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Schema ---
class ChatRequest(BaseModel):
    customer_message: str

# --- Endpoints ---

@app.post("/api/triage/chat/")
async def ai_triage_dispatch(request: ChatRequest, db: Session = Depends(get_db)):
    """Receives customer text, processes with AI, and returns a work order."""

    work_order_data = await generate_work_order(request.customer_message)

    if not work_order_data:
        raise HTTPException(status_code=500, detail="AI processing failed.")

    return {
        "status": "success",
        "dispatch": work_order_data
    }

@app.get("/health")
def health_check():
    return {
        "status": "Backend is running, Database is connected."
    }