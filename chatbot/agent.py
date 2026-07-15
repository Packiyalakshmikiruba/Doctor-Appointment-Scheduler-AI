"""
chatbot/agent.py
Wires all tools together into a LangChain agent with safety-first routing:
    1. Emergency keywords -> deterministic escalation, bypasses agent entirely
    2. Otherwise -> agent picks from: search_doctor, check_doctor_availability,
       book_appointment, predict_noshow_risk, hospital_info_search
"""

import os
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from .tools import search_doctor, check_doctor_availability, book_appointment, predict_noshow_risk
from .rag_tool import hospital_info_search

EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "severe bleeding",
    "unconscious", "suicide", "overdose", "stroke", "heart attack",
    "difficulty breathing", "severe pain", "collapsed", "seizure",
]

SYSTEM_PROMPT = """You are a clinic front-desk assistant for a hospital appointment system.
You have tools to search doctors, check availability, book appointments,
predict no-show risk, and answer general hospital questions.

STRICT RULES:
- NEVER diagnose a condition or suggest medications/dosages.
- NEVER interpret lab results or medical images.
- If the user describes symptoms, acknowledge briefly and suggest booking
  an appointment with the relevant department -- do not speculate on diagnosis.
- Keep responses short, warm, and professional.
- Always confirm key booking details (doctor, date, time) back to the user
  before/after calling book_appointment.
"""

TOOLS = [search_doctor, check_doctor_availability, book_appointment, predict_noshow_risk, hospital_info_search]

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.3,
        )
        _agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_PROMPT)
    return _agent


def is_emergency(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in EMERGENCY_KEYWORDS)


def get_agent_response(message: str, history: list = None):
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
    messages = history + [{"role": "user", "content": message}]

    result = agent.invoke({"messages": messages})
    reply_message = result["messages"][-1]
    reply = reply_message.content

    updated_history = messages + [{"role": "assistant", "content": reply}]
    return reply, updated_history