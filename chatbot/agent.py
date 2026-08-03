import os
import re
import time

from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage

from chatbot.rag_tool import hospital_info_search
from chatbot.tools import (
    search_doctor, doctor_full_details, check_doctor_availability, cancel_appointment,
    reschedule_appointment, appointment_history, get_billing_info,
    symptom_to_department, patient_summary, doctor_summary,
    hospital_statistics, view_medical_records, create_prescription,
)

# -----------------------------------------------------------------------
# PATIENT chat is now INFORMATION-ONLY: search doctors, check availability,
# see appointment history, check bills, symptom -> department, hospital
# FAQs. No booking tools at all -- actual booking happens through the real
# appointment form (100% reliable, no LLM involved). This removes the
# entire class of "wrong doctor / hallucinated date-time / fake booking
# success" bugs, since the chatbot never carries booking state across
# turns anymore.
# -----------------------------------------------------------------------
PATIENT_TOOLS = [
    search_doctor, doctor_full_details, check_doctor_availability, appointment_history,
    get_billing_info, symptom_to_department, hospital_info_search,
]

DOCTOR_TOOLS = [
    search_doctor, check_doctor_availability, cancel_appointment,
    reschedule_appointment, appointment_history, get_billing_info,
    hospital_info_search, doctor_summary, view_medical_records,
    create_prescription,
]

ADMIN_TOOLS = [
    search_doctor, check_doctor_availability, cancel_appointment,
    reschedule_appointment, appointment_history, get_billing_info,
    symptom_to_department, patient_summary, doctor_summary,
    hospital_statistics, hospital_info_search, view_medical_records,
    create_prescription,
]

TOOLS_BY_ROLE = {
    "PATIENT": PATIENT_TOOLS,
    "DOCTOR": DOCTOR_TOOLS,
    "ADMIN": ADMIN_TOOLS,
}

# Real path from appointments/urls.py: path("appointment/add/", ..., name="appointment_create")
BOOKING_FORM_URL = "/appointment/add/"

SYSTEM_PROMPT = f"""
You are a friendly AI Hospital Receptionist. You help patients with
INFORMATION ONLY: searching doctors, checking availability, viewing their
appointment history, checking bills, symptom-to-department guidance, and
hospital FAQs.


STRICT RULES:
- You CANNOT book, cancel, or reschedule appointments. Never say an
  appointment is booked, confirmed, or that the user "has" an appointment.
- If the patient wants to book an appointment, tell them to use the
  appointment booking page at {BOOKING_FORM_URL}, and mention the doctor
  name/department you found (if any) so they know who to select there.
- Always call search_doctor to find a doctor -- never make up a doctor's
  name or ID. If a tool returns no result, say so plainly.
- If a symptom is mentioned (fever, headache, pain, etc.), call symptom_to_department
  first, then search_doctor with that department. Once you've found a doctor to
  recommend, call doctor_full_details with their name to also tell the patient
  their availability (days/times) and consultation fee.
- Never diagnose or prescribe. Reply in the same language the user used.
- If the user just replies "yes"/"ok"/similar after you already recommended a
  doctor, do NOT search again or mention a different doctor. Simply remind
  them of the booking page link for the doctor you already found.
"""

_agents = {}

def _get_agent(role="PATIENT"):
    role = role if role in TOOLS_BY_ROLE else "PATIENT"
    if role not in _agents:
        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=400,
            timeout=20,
            max_retries=1,
        )
        _agents[role] = create_agent(llm, TOOLS_BY_ROLE[role], system_prompt=SYSTEM_PROMPT)
    return _agents[role]

def build_role_context(patient_id, doctor_id, role):
    if role == "PATIENT": return f"\nRole : PATIENT\nPatient ID : {patient_id}\n"
    if role == "DOCTOR": return f"\nRole : DOCTOR\nDoctor ID : {doctor_id}\n"
    return "\nRole : ADMIN\n"
SYMPTOM_KEYWORDS = [
    "fever", "cold", "cough", "pain", "headache", "vali", "vayathu",
    "eruggu", "achu", "kastam", "ache", "sick",
]

# Word-boundary matching so short/common substrings (e.g. "vali") don't
# false-positive inside unrelated words (e.g. "availability" contains "vali").
_SYMPTOM_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SYMPTOM_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

HOSPITAL_INFO_KEYWORDS = [
    "hospital hour", "hospital time", "closing time", "opening time",
    "visiting hour", "hospital address", "hospital location", "hospital detail",
    "contact number", "parking", "hospital timing", "hospital open",
    "hospital", "opd", "clinic hour", "clinic open", "clinic time",
    "monday open", "tuesday open", "wednesday open", "thursday open",
    "friday open", "saturday open", "sunday open", "working day",
    "holiday", "cancellation polic", "reschedule polic",
]

BOOKING_KEYWORDS = [
    "book", "appointment fix", "fix appointment", "confirm my appointment",
    "confirm booking", "want to book", "schedule appointment",
]

HISTORY_KEYWORDS = [
    "medical report", "medical record", "medical history", "past appointment",
    "appointment history", "previous visit", "my history", "which doctor",
    "who did i see", "previous doctor", "last doctor", "parthanga", "paartha",
    "munnadi", "before doctor",
]

def _call_tool(tool_obj, arg):
    """Calls an @tool-decorated LangChain tool directly, bypassing the LLM entirely."""
    return tool_obj.func(arg)


def _is_tamil_script(text: str) -> bool:
    """True if the message contains actual Tamil Unicode characters."""
    return bool(re.search(r"[\u0B80-\u0BFF]", text))


def _translate_to_tamil(english_text: str) -> str:
    """
    Translates an already-correct English reply into Tamil. This is a
    bounded, low-risk use of the LLM -- it is only asked to translate facts
    that were already fetched deterministically from the database, never
    to decide or invent any fact itself. If the call fails for any reason
    (rate limit, etc.), the original English text is returned so the user
    still gets a correct answer.
    """
    try:
        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=500,
            timeout=15,
            max_retries=1,
        )
        result = llm.invoke([
            {
                "role": "system",
                "content": (
                    "Translate the user's text into Tamil script. Keep all names, "
                    "numbers, dates, times, and IDs EXACTLY unchanged. Do not add, "
                    "remove, or explain anything -- output only the Tamil translation."
                ),
            },
            {"role": "user", "content": english_text},
        ])
        return result.content.strip() or english_text
    except Exception:
        return english_text


def deterministic_router(message: str, user_role: str, patient_id=None) -> str | None:
    """
    Fast, reliable, non-LLM routing for the most common patient questions.
    Returns a reply string if handled here, or None to fall through to the
    LLM agent for genuinely open-ended queries. This exists because the
    free-tier Groq model is unreliable at deciding WHEN to call tools --
    so for these common intents, we skip that decision entirely.
    """
    if user_role != "PATIENT":
        return None

    text = message.lower()

    # 1. Specific doctor name mentioned (e.g. "Dr. Arun Raj") -- checked
    #    BEFORE the symptom check, since a question like "Dr. X availability"
    #    is a more specific intent than a generic symptom mention.
    name_match = re.search(r"dr\.?\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text)
    if name_match:
        full_name = name_match.group(1).strip()
        # Search by the first name token only -- first_name/last_name are
        # separate DB fields, so querying "arun raj" as one string matches
        # neither ("Arun Raj" split across two columns never contains the
        # substring "arun raj" in either column individually).
        search_term = full_name.split()[0]
        result = _call_tool(search_doctor, search_term)

        if "today" in text or "available" in text or "avail" in text or "time" in text:
            id_match = re.search(r"Doctor ID\s*:\s*(\d+)", result)
            if id_match:
                availability = _call_tool(check_doctor_availability, int(id_match.group(1)))
                return f"{result}\n\n{availability}"

        return result

    # 2. Booking intent (e.g. "appointment fix pannunga", "book an appointment")
    #    -- typo-tolerant: matches "appointment"/"appoinment"/"appinment" etc.
    #    Checked before hospital-info so a booking request never gets an
    #    unhelpful generic reply; the chatbot can't book, so it should
    #    always clearly point to the real booking form.
    if (
        re.search(r"\bbook\b", text)
        or (re.search(r"\bfix\b", text) and re.search(r"appo?i?nt?ment", text))
        or any(kw in text for kw in BOOKING_KEYWORDS)
    ):
        return (
            "I can't book appointments directly in chat, but I can help you get there. "
            f"Please visit {BOOKING_FORM_URL} to book your appointment -- if you tell me "
            "the doctor or department you want, I'll confirm they're available first."
        )

    # 3. Hospital details (hours, location, contact, parking, etc.)
    if any(kw in text for kw in HOSPITAL_INFO_KEYWORDS):
        return _call_tool(hospital_info_search, message)

    # 4. Medical reports / appointment history
    if any(kw in text for kw in HISTORY_KEYWORDS):
        if not patient_id:
            return "I couldn't find your patient profile. Please contact admin."
        return _call_tool(appointment_history, patient_id)

    # 5. Symptom mentioned -> always resolve department + search doctors
    if _SYMPTOM_PATTERN.search(text):
        dept_result = _call_tool(symptom_to_department, message)
        # Extract department name from the tool's response text
        dept_match = re.search(r"department:\s*(.+)", dept_result, re.IGNORECASE)
        department = dept_match.group(1).strip() if dept_match else "General Medicine"

        doctors = _call_tool(search_doctor, department)
        return (
            f"{dept_result}\n\n{doctors}\n\n"
            f"To book, visit the appointment page and select one of these doctors."
        )

    return None



def get_agent_response(message, history=None, patient_id=None, doctor_id=None, user_role="PATIENT", session_key=None):
    history = history or []

    # FIX: deterministic_router was defined above but never actually
    # called anywhere -- it existed purely as dead code. This is exactly
    # why "i have fever" (and every other symptom keyword) skipped the
    # fast, reliable direct-tool-call path and went straight to the
    # unreliable LLM instead, which then hallucinated a doctor name and
    # got caught by the anti-hallucination guard below, producing the
    # generic "Could you tell me the department or symptom again?" reply.
    router_reply = deterministic_router(message, user_role, patient_id=patient_id)
    if router_reply is not None:
        if _is_tamil_script(message):
            router_reply = _translate_to_tamil(router_reply)
        history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": router_reply},
        ])
        return router_reply, history

    context = build_role_context(patient_id, doctor_id, user_role)
    agent = _get_agent(user_role)

    invoke_input = {
        "messages": history[-3:] + [{"role": "user", "content": context + "\n\n" + message}]
    }

    def _invoke_with_retry():
        # Groq's free "on_demand" tier has a low tokens-per-minute limit,
        # so back-to-back chat messages can hit a 429 rate_limit_exceeded
        # error even when nothing is actually wrong. Groq's error message
        # tells us exactly how long to wait ("please try again in 10.4s") --
        # so wait that long and retry (up to 2 attempts) instead of
        # immediately giving up.
        last_err = None
        for attempt in range(2):
            try:
                return agent.invoke(invoke_input)
            except Exception as e:
                last_err = e
                err_text = str(e)
                if "rate_limit" in err_text or "429" in err_text:
                    wait_match = re.search(r"try again in ([\d.]+)s", err_text)
                    wait_seconds = float(wait_match.group(1)) if wait_match else 4.0
                    time.sleep(min(wait_seconds, 15) + 0.5)
                    continue
                raise
        raise last_err

    try:
        result = _invoke_with_retry()
        reply = result["messages"][-1].content

        # Tool results are deterministic strings the tool itself generated
        # (e.g. "Doctor ID: 7 ..."), unlike `reply` which is the LLM's own
        # paraphrase. Use this turn's actual tool output to verify the
        # model isn't just inventing a doctor name from chat history.
        tool_outputs = "\n".join(
            m.content for m in result["messages"] if isinstance(m, ToolMessage)
        )

        # Detect if the model leaked raw tool-call syntax instead of
        # actually executing the tool. Two formats seen in practice:
        #   <function=name>{...}</function>
        #   <tool_name>{...}</tool_name>   (e.g. <hospital_info_search>{...}</hospital_info_search>)
        _leaked_tool_call = re.search(r"<(\w+)>\s*\{.*?\}\s*</\1>", reply, re.DOTALL)
        if "<function=" in reply or "</function>" in reply or _leaked_tool_call:
            reply = (
                "Sorry, I had trouble processing that. Could you rephrase, "
                "or tell me the doctor name/department you're looking for?"
            )

        # The model sometimes mentions "Dr. Someone" purely from its own
        # chat-history recollection WITHOUT actually calling search_doctor
        # this turn (e.g. replying to a plain "yes"/"ok") -- this is exactly
        # how a different, invented doctor name keeps showing up. If this
        # turn's tool output contains no doctor lookup result at all, any
        # "Dr. X" in the reply is ungrounded -- discard it.
        elif (
            re.search(r"Dr\.?\s+[A-Za-z]", reply)
            and "doctor id" not in tool_outputs.lower()
            and "doctor name" not in tool_outputs.lower()
        ):
            reply = (
                "Could you tell me the department or symptom again so I can "
                "search our doctors properly?"
            )

    except Exception as e:
        print("Agent invoke failed:", e)
        err_text = str(e)
        if "rate_limit" in err_text or "429" in err_text:
            reply = (
                "I'm getting a lot of requests right now and hit a rate limit. "
                "Please wait about 10 seconds and send your message again."
            )
        else:
            reply = (
                "Sorry, I didn't quite understand that. Could you tell me "
                "which department, doctor, or symptom you'd like help with?"
            )

    history.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ])

    return reply, history