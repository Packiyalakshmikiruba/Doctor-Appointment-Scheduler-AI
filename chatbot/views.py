"""
chatbot/views.py
Django views for the chat widget and its API endpoint.

URLs expected (already in your config/urls.py):
    chat/      -> chat_widget   (renders the widget page)
    api/chat/  -> chat_api      (receives messages, returns agent replies)
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .agent import get_agent_response

# Simple in-memory session store: {session_key: [{"role":..., "content":...}, ...]}
# Fine for a student/demo project. For production, back this with Redis/DB
# (e.g. a checkpointer, since create_agent supports LangGraph checkpointing).
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

    try:
        reply, updated_history = get_agent_response(user_message, history=history)
        _SESSION_HISTORY[session_key] = updated_history
    except Exception as exc:  # noqa: BLE001 - surface a safe message to the widget
        return JsonResponse(
            {"error": "Something went wrong talking to the assistant.", "detail": str(exc)},
            status=500,
        )

    return JsonResponse({"response": reply})
