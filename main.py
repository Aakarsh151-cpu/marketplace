from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import engine, get_db
from ai.ghost_assistant import generate_work_order

# Create the database tables automatically for MVP
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillGrid Backend API")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allows your Next.js app to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Schemas ---
class ChatRequest(BaseModel):
    customer_message: str

# --- Endpoints ---

@app.post("/api/triage/chat/")
async def ai_triage_dispatch(request: ChatRequest, db: Session = Depends(get_db)):
    """Receives customer text, hits the AI, and returns a work order."""
    
    # 1. Ask the Ghost Assistant to analyze the text
    work_order_data = await generate_work_order(request.customer_message)
    
    if not work_order_data:
        raise HTTPException(status_code=500, detail="AI processing failed.")
    
    # 2. In a full production flow, you would save this to the Bookings table here.
    # For now, we return it directly to the Next.js frontend to prove the loop works.
    
    return {
        "status": "success",
        "dispatch": work_order_data
    }

@app.get("/health")
def health_check():
    return {"status": "Backend is running, Database is connected."}