import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, ValidationError
import asyncio
import enum

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
except ModuleNotFoundError:
    logger.warning("groq package not installed; falling back to default AI behavior")
    AsyncGroq = None
    client = None


# ================================
# 🔐 ENUMS
# ================================
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


# ================================
# 📦 SCHEMAS
# ================================
class WorkOrderSchema(BaseModel):
    category: CategoryEnum
    urgency: UrgencyEnum
    summary_for_technician: str

    estimated_labor: int
    estimated_parts: int
    bill_of_materials: List[str]


class VisionAuditSchema(BaseModel):
    is_verified: bool
    audit_notes: str
    fraud_detected: bool


# ================================
# 🧠 WORK ORDER GENERATOR
# ================================
async def generate_work_order(customer_message: str) -> Optional[dict]:

    system_prompt = """
    You are the 'Ghost Assistant', an elite autonomous dispatch broker.

    Analyze the issue and output STRICT JSON.

    PRICING RULES:
    - Labor ₹300–₹800
    - Estimate parts realistically
    """

    if client is None:
        logger.warning("No groq client available; returning fallback work order.")
        return {
            "category": "UNKNOWN",
            "urgency": "ROUTINE",
            "summary_for_technician": "Manual inspection required",
            "estimated_labor": 300,
            "estimated_parts": 0,
            "bill_of_materials": []
        }

    try:
        response = await client.chat.completions.create(
            model="llama3-8b-8192",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": customer_message}
            ],
        )

        raw_text = response.choices[0].message.content

        data = json.loads(raw_text)
        validated = WorkOrderSchema(**data)

        return validated.model_dump()

    except Exception as e:
        logger.error(f"WorkOrder AI failed: {str(e)}")
        return None


# ================================
# 🔁 RETRY WRAPPER
# ================================
async def generate_with_retry(customer_message: str, retries=2):
    for _ in range(retries):
        result = await generate_work_order(customer_message)
        if result:
            return result
        await asyncio.sleep(1)

    return {
        "category": "UNKNOWN",
        "urgency": "ROUTINE",
        "summary_for_technician": "Manual inspection required",
        "estimated_labor": 300,
        "estimated_parts": 0,
        "bill_of_materials": []
    }


# ================================
# 👁️ VISION AUDIT SYSTEM
# ================================
async def verify_technician_work(
    base64_image: str,
    original_bom: List[str]
) -> dict:

    system_prompt = f"""
    You are an elite QA AI for a home services marketplace.

    Expected materials: {original_bom}

    Analyze the image and verify work completion.

    RULES:
    - Detect missing components
    - Detect fake or incomplete work
    - Be strict (avoid false positives)

    OUTPUT JSON:
    {{
      "is_verified": true|false,
      "audit_notes": "1-line explanation",
      "fraud_detected": true|false
    }}
    """

    try:
        response = await client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Audit this technician work."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
        )

        raw_text = response.choices[0].message.content

        data = json.loads(raw_text)
        validated = VisionAuditSchema(**data)

        return validated.model_dump()

    except ValidationError as ve:
        logger.error(f"Vision validation failed: {ve}")

    except Exception as e:
        logger.error(f"Vision audit failed: {str(e)}")

    # 🚨 Safe fallback
    return {
        "is_verified": False,
        "audit_notes": "AI audit failed. Manual review required.",
        "fraud_detected": False
    }


# ================================
# 🔁 RETRY FOR VISION
# ================================
async def verify_with_retry(base64_image: str, bom: List[str], retries=2):
    for _ in range(retries):
        result = await verify_technician_work(base64_image, bom)
        if result:
            return result
        await asyncio.sleep(1)

    return {
        "is_verified": False,
        "audit_notes": "Repeated AI failure. Manual inspection needed.",
        "fraud_detected": False
    }