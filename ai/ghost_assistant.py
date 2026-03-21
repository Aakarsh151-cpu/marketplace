import httpx
import json
import logging
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# 1. The Strict Output Schema
class WorkOrderSchema(BaseModel):
    category: str
    urgency: str
    summary_for_technician: str

async def generate_work_order(customer_message: str) -> dict | None:
    """Sends the customer request to local Ollama and guarantees JSON output."""
    
    system_prompt = """
    You are the 'Ghost Assistant', an autonomous dispatch brain for an Indian home services marketplace.
    Read the customer complaint and output STRICT JSON matching this schema exactly:
    {"category": "AC_REPAIR|PLUMBING|ELECTRICAL|OUTSTATION_CAB|UNKNOWN", "urgency": "CRITICAL|HIGH|ROUTINE", "summary_for_technician": "A 1-sentence technical summary"}
    Do not output any markdown formatting, conversational text, or explanations. Just the JSON object.
    """

    payload = {
        "model": "mistral",
        "prompt": f"{system_prompt}\nCustomer: {customer_message}",
        "stream": False,
        "format": "json" # Forces Ollama to lock into JSON mode
    }

    try:
        # Use httpx for asynchronous requests so your server doesn't freeze while the AI thinks
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:11434/api/generate", json=payload, timeout=20.0)
            response.raise_for_status()
            
            raw_ai_text = response.json().get("response", "{}")
            ai_data_dict = json.loads(raw_ai_text)
            
            # Validate the AI's output against our Pydantic schema
            validated_order = WorkOrderSchema(**ai_data_dict)
            return validated_order.model_dump()

    except (httpx.RequestError, json.JSONDecodeError, ValidationError) as e:
        logger.error(f"Ghost Dispatcher Failed: {str(e)}")
        return None