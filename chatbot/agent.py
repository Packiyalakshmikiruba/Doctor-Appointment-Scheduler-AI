"""
chatbot/agent.py
Wires all tools together into a LangChain agent with safety-first routing:
    1. Emergency keywords (English + Tamil + Tanglish) -> deterministic
       escalation, bypasses agent entirely -- fast, free, no LLM call.
    2. Otherwise -> agent picks from: search_doctor, check_doctor_availability,
       book_appointment, predict_noshow_risk, hospital_info_search, get_billing_info
       (agent already understands any language/spelling via the LLM itself).
"""

import os
from datetime import date
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from .tools import search_doctor, check_doctor_availability, book_appointment, predict_noshow_risk, get_billing_info
from .rag_tool import hospital_info_search

EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "can't breathe", "cannot breathe", "severe bleeding",
    "unconscious", "suicide", "overdose", "stroke", "heart attack",
    "difficulty breathing", "severe pain", "collapsed", "seizure",

    # Tanglish (Tamil words typed in English letters)
    "nenju vali", "moochu vidamudiyala", "moochu thinaral",
    "ratha kasivu", "mayakkam", "thatrkolai", "swasa pirachanai",
    "romba vali", "udal nadukkam", "hrudaya kaettu",

    # Tamil script
    "நெஞ்சு வலி", "மூச்சு விடமுடியல", "மூச்சு திணறல்", "மயக்கம்",
    "இரத்த கசிவு", "தற்கொலை", "சுவாசப் பிரச்சனை", "மார்பு வலி",
    "உடல் நடுக்கம்", "இதய கோளாறு",
]

SYSTEM_PROMPT = """You are a clinic front-desk assistant for a hospital appointment system.
You have EXACTLY these 6 tools available: search_doctor, check_doctor_availability,
book_appointment, predict_noshow_risk, hospital_info_search, get_billing_info.

CRITICAL: Never attempt to call any tool other than these 6. You do NOT have
web search, browsing, or any external tool access. If you need information
not covered by these tools, use hospital_info_search or ask the user for
clarification instead.

IMPORTANT: When calling tools (especially book_appointment), always use
English internally for the tool call itself, even if you reply to the user
in Tamil or Tanglish afterward. Tool parameters must be in the exact format
specified (YYYY-MM-DD dates, HH:MM 24-hour times).

LANGUAGE RULE:
- Always reply in the SAME language and style the user writes in.
- If the user writes in Tamil, reply in Tamil.
- If the user writes in Tanglish (Tamil words in English letters), reply in Tanglish the same way.
- If the user writes in English, reply in English.
- Never switch languages on your own -- match the user's most recent message.
- Understand booking requests even with spelling mistakes or mixed language phrasing.
- If the user's request is ambiguous (e.g. no department or doctor mentioned),
  ask a clarifying question instead of guessing or trying unavailable tools.

STRICT RULES:
- NEVER diagnose a condition or suggest medications/dosages.
- NEVER interpret lab results or medical images.
- If the user describes symptoms, acknowledge briefly and suggest booking
  an appointment with the relevant department -- do not speculate on diagnosis.
- Keep responses short, warm, and professional.
- Always confirm key booking details (doctor, date, time) back to the user
  before/after calling book_appointment.
"""

TOOLS = [
    search_doctor,
    check_doctor_availability,
    book_appointment,
    predict_noshow_risk,
    hospital_info_search,
    get_billing_info,
]

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.3,
        )
        _agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_PROMPT)
    return _agent


def is_emergency(message: str) -> bool:
    """
    Fast, deterministic, zero-latency safety check.
    Runs BEFORE the LLM agent -- so emergency routing never depends
    on model output and can't be hallucinated around.
    """
    text = message.lower()
    return any(kw in text for kw in EMERGENCY_KEYWORDS)


def get_agent_response(message: str, history: list = None, patient_id: int = None):
    """
    Returns: (reply: str, updated_history: list)
    """
    history = history or []

    if is_emergency(message):
        reply = ("This sounds urgent. I'm connecting you to clinic staff "
                  "right now -- please call our front desk immediately or "
                  "visit the nearest emergency room if this is life-threatening.")
        return reply, history

    if not os.environ.get("GROQ_API_KEY"):
        reply = ("I can help with booking, doctor search, and hospital info once "
                  "the assistant is fully configured. For now, please use the menu "
                  "options to book an appointment or browse doctors.")
        return reply, history

    agent = _get_agent()

    today_str = date.today().strftime("%Y-%m-%d")
    context_note = f"[System note: today's date is {today_str}. Use this to resolve relative dates like 'tomorrow' or 'next Monday'.]\n\n"

    if patient_id:
        context_note += (
            f"[System note: the logged-in patient's patient_id is {patient_id}. "
            f"Use this automatically when calling book_appointment -- "
            f"never ask the user for their patient_id.]\n\n"
        )

    messages = history + [{"role": "user", "content": context_note + message}]

    try:
        result = agent.invoke({"messages": messages})
        reply_message = result["messages"][-1]
        reply = reply_message.content

        # Detect if the model leaked raw tool-call syntax instead of
        # actually executing the tool (happens occasionally with smaller
        # models mixing non-English replies with tool calling).
        if "<function=" in reply or "</function>" in reply:
            reply = ("Sorry, I had trouble processing that request. Could you "
                      "please confirm the doctor, date, and time again?")

    except Exception:
        # Model attempted an invalid/hallucinated tool call -- fail gracefully
        # instead of crashing the whole chat.
        reply = ("Sorry, I didn't quite understand that. Could you tell me "
                  "which department or doctor you'd like to book with, and "
                  "your preferred date?")

    updated_history = messages + [{"role": "assistant", "content": reply}]
    return reply, updated_history