"""
chatbot/views.py
Django views for the chat widget and its API endpoint.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .agent import get_agent_response

# Simple in-memory session store. Fine for demo; use Redis/DB for production.
_SESSION_HISTORY = {}


def chat_widget(request):
    return render(request, "chatbot/chat_widget.html")


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    user_message = body.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "message is required"}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    history = _SESSION_HISTORY.get(session_key, [])
    history = history[-10:]

    patient_id = None
    doctor_id = None
    user_role = None

    if request.user.is_authenticated:
        user_role = getattr(request.user, "role", None)

        if user_role == "PATIENT":
            patient = getattr(request.user, "patient_profile", None)
            if patient:
                patient_id = patient.id

        elif user_role == "DOCTOR":
            doctor = getattr(request.user, "doctor_profile", None)
            if doctor:
                doctor_id = doctor.id

    try:
        reply, updated_history = get_agent_response(
            user_message,
            history=history,
            patient_id=patient_id,
            user_role=user_role,
            doctor_id=doctor_id,
        )
        _SESSION_HISTORY[session_key] = updated_history[-20:]

    except Exception as exc:
        print("=" * 60)
        print("CHATBOT ERROR")
        print(exc)
        print("=" * 60)

        return JsonResponse(
            {
                "error": "Assistant Error",
                "detail": str(exc),
            },
            status=500,
        )

    # Success path -- this was missing entirely before, which is why
    # a working reply never made it back to the browser.
    return JsonResponse({"response": reply})