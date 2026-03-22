import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from groq import AsyncGroq
import asyncio
import enum

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))


# 🔐 Enums (strict control)
class CategoryEnum(str, enum.Enum):
    AC_REPAIR = "AC_REPAIR"
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    OUTSTATION_CAB = "OUTSTATION_CAB"
    UNKNOWN = "UNKNOWN"


class UrgencyEnum(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"


# 📦 Strong Schema
class WorkOrderSchema(BaseModel):
    category: CategoryEnum
    urgency: UrgencyEnum
    summary_for_technician: str

    estimated_labor: int
    estimated_parts: int
    bill_of_materials: List[str]


# 🧠 Main AI function
async def generate_work_order(customer_message: str) -> Optional[dict]:

    system_prompt = """
    You are the 'Ghost Assistant', an elite autonomous dispatch broker for an Indian home services marketplace.

    Analyze the customer complaint and generate STRICT JSON.

    PRICING RULES (INR):
    - Labor: ₹300–₹800 typical
    - Estimate realistic parts cost
    - If no parts → 0

    OUTPUT FORMAT:
    {
      "category": "AC_REPAIR|PLUMBING|ELECTRICAL|OUTSTATION_CAB|UNKNOWN",
      "urgency": "CRITICAL|HIGH|ROUTINE",
      "summary_for_technician": "1-line technical diagnosis",
      "estimated_labor": 400,
      "estimated_parts": 1200,
      "bill_of_materials": ["item1", "item2"]
    }
    """

    try:
        response = await client.chat.completions.create(
            model="llama3-8b-8192",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": customer_message}
            ],
            model="llama3-8b-8192",
            temperature=0.2, # Low temperature keeps it analytical and less creative
            response_format={"type": "json_object"} # Forces Groq to lock into JSON mode
        )
        
        # Extract the text and parse it
        raw_ai_text = chat_completion.choices[0].message.content
        ai_data_dict = json.loads(raw_ai_text)
        
        # Validate against our Pydantic schema to ensure it didn't hallucinate
        validated_order = WorkOrderSchema(**ai_data_dict)
        return validated_order.model_dump()

    except Exception as e:
        logger.error(f"Groq API failed: {str(e)}")
        return None
