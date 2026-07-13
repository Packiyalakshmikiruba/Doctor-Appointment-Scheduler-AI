"""
llm_engine.py
-------------
Spec Section 4: LLM Model API Integration
- Prompt engineering & context management for safe symptom parsing
- Deterministic fallback pipeline for critical alerts (Section 5)

Design: emergency keyword detection and FAQ matching happen BEFORE
any LLM call -- so life-critical routing never depends on model output
and can never be hallucinated around.
"""

import os

# ---- Deterministic safety layer (bypasses LLM entirely) ----
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "severe bleeding",
    "unconscious", "suicide", "overdose", "stroke", "heart attack",
    "difficulty breathing", "severe pain", "collapsed", "seizure",
]

FAQ_RESPONSES = {
    "timing": "Our clinic is open Monday to Saturday, 9 AM to 6 PM.",
    "location": "You can find our clinic address on the Contact page.",
    "cancel": "You can cancel or reschedule from the 'My Appointments' page.",
    "reminder": "SMS reminders are sent 24 hours before your appointment.",
    "fee": "Consultation fees vary by doctor -- check the Doctor list for exact pricing.",
}

# ---- System prompt: Prompt Engineering & Context Management (Spec 4) ----
SYSTEM_PROMPT = """You are a clinic front-desk assistant for a hospital appointment system.
You help patients with:
- booking, rescheduling, or cancelling appointments
- answering FAQs about clinic timings, location, fees, and policies
- routing symptom-related messages to the appropriate department

STRICT RULES (never break these):
- NEVER diagnose a condition or suggest medications/dosages.
- NEVER interpret lab results, prescriptions, or medical images.
- If the user describes symptoms, acknowledge briefly and say a doctor
  will review during the appointment; offer to help book one.
- If anything sounds urgent or you are unsure, say you are connecting
  them to clinic staff immediately.
- Keep responses short (2-3 sentences), warm, and professional.
"""


def is_emergency(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in EMERGENCY_KEYWORDS)


def match_faq(message: str):
    text = message.lower()
    if any(w in text for w in ["timing", "hours", "open", "close"]):
        return FAQ_RESPONSES["timing"]
    if any(w in text for w in ["where", "location", "address"]):
        return FAQ_RESPONSES["location"]
    if any(w in text for w in ["cancel", "reschedule"]):
        return FAQ_RESPONSES["cancel"]
    if "reminder" in text or "sms" in text:
        return FAQ_RESPONSES["reminder"]
    if "fee" in text or "cost" in text or "price" in text:
        return FAQ_RESPONSES["fee"]
    return None


def call_llm(message: str, history: list) -> str:
    """
    Real LLM API call. Wire up OpenAI / HuggingFace / Anthropic here.
    Reads API key from environment variable -- never hardcode keys.

    Example (OpenAI):
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history +
                     [{"role": "user", "content": message}],
            max_tokens=200,
        )
        return resp.choices[0].message.content

    Example (HuggingFace, free tier via Inference API):
        import requests
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {os.environ['HF_API_KEY']}"}
        payload = {"inputs": f"{SYSTEM_PROMPT}\\nUser: {message}\\nAssistant:"}
        resp = requests.post(API_URL, headers=headers, json=payload)
        return resp.json()[0]["generated_text"]
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Fallback used when no API key is configured (dev/demo mode)
        return ("Thanks for your message! I can help you book an appointment, "
                "answer clinic FAQs, or connect you to staff. Could you tell me "
                "a bit more about what you need?")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:  # keep last 6 turns -- context window management
        messages.append(h)
    messages.append({"role": "user", "content": message})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=200,
        temperature=0.4,
    )
    return resp.choices[0].message.content


def get_bot_response(message: str, history: list = None) -> dict:
    """
    Deterministic fallback pipeline (Spec Section 5):
    1. Emergency keywords -> always escalate, bypass LLM
    2. FAQ match -> deterministic answer, no hallucination risk
    3. Otherwise -> LLM handles general conversation
    """
    history = history or []

    if is_emergency(message):
        return {
            "reply": ("This sounds urgent. I'm connecting you to clinic staff "
                       "right now -- please call our front desk immediately or "
                       "visit the nearest emergency room if this is life-threatening."),
            "escalated": True,
        }

    faq = match_faq(message)
    if faq:
        return {"reply": faq, "escalated": False}

    reply = call_llm(message, history)
    return {"reply": reply, "escalated": False}