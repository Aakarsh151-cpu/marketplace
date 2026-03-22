import os
import json
import logging
from pydantic import BaseModel, ValidationError
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# Initialize the Groq Client (it automatically looks for the GROQ_API_KEY environment variable)
# We use AsyncGroq so your server doesn't freeze while the AI is thinking
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

class WorkOrderSchema(BaseModel):
    category: str
    urgency: str
    summary_for_technician: str

async def generate_work_order(customer_message: str) -> dict | None:
    """Sends the customer request to Groq Cloud LLM and guarantees JSON output."""
    
    system_prompt = """
    You are the 'Ghost Assistant', an autonomous dispatch brain for an Indian home services marketplace.
    Read the customer complaint and output STRICT JSON matching this exact structure:
    {"category": "AC_REPAIR|PLUMBING|ELECTRICAL|OUTSTATION_CAB|UNKNOWN", "urgency": "CRITICAL|HIGH|ROUTINE", "summary_for_technician": "A clear, 1-sentence technical summary"}
    """

    try:
        # We use llama3 because it is incredibly fast and highly obedient with JSON
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": customer_message}
            ],
            model="llama-3.1-8b-instant",
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
        logger.error(f"Groq Dispatcher Failed: {str(e)}")
        return None
