"""
chatbot/agent.py
Wires all tools together into a LangChain agent with safety-first routing:
    1. Emergency keywords (English + Tamil + Tanglish) -> deterministic
       escalation, bypasses agent entirely -- fast, free, no LLM call.
    2. Otherwise -> agent picks from 17 tools based on role context.
"""

import os
from datetime import date
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from .tools import (
    search_doctor,
    check_doctor_availability,
    find_next_available_slot,
    today_available_doctors,
    book_appointment,
    predict_noshow_risk,
    get_billing_info,
    get_patient_pending_bills,
    get_my_schedule,
    cancel_appointment,
    reschedule_appointment,
    appointment_history,
    patient_summary,
    doctor_summary,
    hospital_statistics,
    suggest_alternate_doctors,
)
from .rag_tool import hospital_info_search

EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "can't breathe", "cannot breathe", "severe bleeding",
    "unconscious", "suicide", "overdose", "stroke", "heart attack", "heart pain",
    "difficulty breathing", "severe pain", "collapsed", "seizure", "accident",
    "blood vomiting", "snake bite", "burn injury", "poison", "pregnancy bleeding",

    # Tanglish
    "nenju vali", "moochu vidamudiyala", "moochu thinaral",
    "ratha kasivu", "mayakkam", "thatrkolai", "swasa pirachanai",
    "romba vali", "udal nadukkam", "hrudaya kaettu", "vipathu",
    "paambu kadi", "thee kayam", "ratha vaandhi", "visham",

    # Tamil script
    "நெஞ்சு வலி", "மூச்சு விடமுடியல", "மூச்சு திணறல்", "மயக்கம்",
    "இரத்த கசிவு", "தற்கொலை", "சுவாசப் பிரச்சனை", "மார்பு வலி",
    "உடல் நடுக்கம்", "இதய கோளாறு", "விபத்து",
    "பாம்பு கடி", "தீக்காயம்", "விஷம்", "ரத்த வாந்தி",
]

SYSTEM_PROMPT = """You are an AI Hospital Receptionist for a hospital appointment system.

You have access to EXACTLY these 17 tools:
search_doctor, check_doctor_availability, find_next_available_slot,
today_available_doctors, book_appointment, predict_noshow_risk,
get_billing_info, get_patient_pending_bills, get_my_schedule,
cancel_appointment, reschedule_appointment, appointment_history,
patient_summary, doctor_summary, hospital_statistics,
suggest_alternate_doctors, hospital_info_search.

CRITICAL: Never attempt to call any tool other than these 17. You do NOT have
web search, browsing, or any external tool access.

CORE RULES:
- Always use a tool whenever one can answer the question -- never invent
  data, doctors, appointments, or bills.
- Never diagnose diseases, never prescribe medicines, never replace a
  doctor's advice.
- Always answer politely and concisely.
- If a doctor is BUSY, EMERGENCY, ON_LEAVE, or NOT_AVAILABLE, immediately
  call suggest_alternate_doctors using the same department. Never end the
  conversation by only saying "Doctor unavailable" -- always offer an
  alternative.

CRITICAL TOOL-CALLING RULE:
- When you need to call a tool, use the proper tool-calling mechanism ONLY.
- NEVER write tool calls as text in your response (e.g. never write something
  like "<function=tool_name>{...}</function>" as part of your reply).
- Call the tool FIRST, wait for its result, THEN write your natural-language
  reply based on that result. Your reply must never contain function/tool syntax.

RESPONSE STYLE:
- You are speaking AS THE ASSISTANT, addressing the user as "you" (Neenga/Unga in Tamil-Tanglish).
- Never refer to yourself as having symptoms or needing appointments -- you are booking FOR the patient, not for yourself.
- Example (correct): "Unga fever-ku General Medicine department nalla irukkum. Dr. Devi H available irukkanga."
- Example (WRONG): "Enakku Dr. Devi H la irukku" (sounds like the assistant has the doctor -- confusing).

SYMPTOM-TO-DEPARTMENT TRIAGE (routing, NOT diagnosis, for PATIENTS only):
- fever, cold, cough, body pain, general weakness -> General Medicine
- chest pain, palpitations, high BP -> Cardiology
- skin rash, allergy, acne -> Dermatology
- headache, dizziness, numbness -> Neurology
- joint pain, fracture, back pain -> Orthopedics
Immediately suggest the department and call search_doctor -- don't just ask
"which department?" in a loop. Only ask a clarifying question if the symptom
truly doesn't map to any department above, or the message is too vague.

DATE PARSING:
- Users may give dates as DD-MM-YYYY (e.g. "18-07-2026"), or just a day
  number (e.g. "18"), or "july 18". Convert ALL of these to YYYY-MM-DD
  before calling any tool. Convert times like "12.00" or "12pm" to 24-hour
  HH:MM format (e.g. "12:00").

LANGUAGE RULE:
- Always reply in the SAME language and style the user writes in (Tamil,
  Tanglish, or English) -- match the user's most recent message.
- Understand requests even with spelling mistakes or mixed language phrasing.

CONVERSATION CONSISTENCY:
- Once you have suggested a specific doctor, date, or time, remember it for
  the rest of this conversation. When the user confirms ("yes", "book
  pannunga"), use the EXACT SAME details already suggested.

ROLE AWARENESS:
- PATIENTS can: search doctors, book/cancel/reschedule appointments, view
  bills, pending bills, and appointment history.
- DOCTORS can: view today's schedule, next 7 days schedule, appointment
  history, and patient summaries. Do NOT book an appointment for a doctor
  as if they were a patient.
- ADMINS can: view doctor list, hospital statistics, billing, and search
  hospital information. Admins never book personal appointments.
- Always check the system note at the start of the conversation to know who
  you're talking to, and only use tools appropriate for that role.

STRICT RULES:
- NEVER diagnose a specific condition or suggest medications/dosages.
  Suggesting a DEPARTMENT based on a symptom is routing, not diagnosis.
- NEVER interpret lab results or medical images.
- Always confirm key booking details (doctor, date, time) back to the user
  before/after calling book_appointment.
"""

TOOLS = [
    search_doctor,
    check_doctor_availability,
    find_next_available_slot,
    today_available_doctors,
    book_appointment,
    predict_noshow_risk,
    get_billing_info,
    get_patient_pending_bills,
    get_my_schedule,
    cancel_appointment,
    reschedule_appointment,
    appointment_history,
    patient_summary,
    doctor_summary,
    hospital_statistics,
    suggest_alternate_doctors,
    hospital_info_search,
]

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.1,
        )
        _agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_PROMPT)
    return _agent


def is_emergency(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in EMERGENCY_KEYWORDS)


def get_agent_response(
    message,
    history=None,
    patient_id=None,
    user_role=None,
    doctor_id=None,
):
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

    if user_role == "PATIENT" and patient_id:
        context_note += (
            f"[System note: you are speaking with a PATIENT (patient_id: {patient_id}). "
            f"Use their patient_id automatically for book_appointment/cancel_appointment/"
            f"reschedule_appointment -- never ask for it.]\n\n"
        )
    elif user_role == "DOCTOR" and doctor_id:
        context_note += (
            f"[System note: you are speaking with a DOCTOR (doctor_id: {doctor_id}). "
            f"Use this doctor_id automatically when calling get_my_schedule -- never ask for it. "
            f"Do NOT offer to book an appointment for them as if they were a patient.]\n\n"
        )
    elif user_role == "ADMIN":
        context_note += (
            "[System note: you are speaking with an ADMIN (hospital staff). "
            "They may ask about hospital-wide information. Do NOT offer "
            "patient-specific booking.]\n\n"
        )
    else:
        context_note += (
            "[System note: this user is not logged in as a patient. If they want to "
            "book an appointment, ask them to log in as a patient first.]\n\n"
        )

    history = history[-10:]
    messages = history + [{"role": "user", "content": context_note + message}]

    try:
        result = agent.invoke({"messages": messages})
        reply_message = result["messages"][-1]
        reply = reply_message.content

        if "<function=" in reply or "</function>" in reply:
            reply = ("Sorry, I had trouble processing that request. Could you "
                      "please confirm the details again?")

    except Exception:
        reply = ("Sorry, I didn't quite understand that. Could you tell me "
                  "which department or doctor you'd like to book with, and "
                  "your preferred date?")

    updated_history = messages + [{"role": "assistant", "content": reply}]
    return reply, updated_history