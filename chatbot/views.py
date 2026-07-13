import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import ChatSession, ChatLog
from .llm_engine import get_bot_response


@login_required
def chat_widget(request):
    if "chat_session_id" not in request.session:
        request.session["chat_session_id"] = str(uuid.uuid4())
    return render(request, "chatbot/chat_widget.html")


@csrf_exempt
@login_required
def chat_api(request):
    """
    Spec Section 5: real-time chat widget backend.
    POST body: {"message": "..."}
    Returns:    {"reply": "...", "escalated": bool}
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body or "{}")
    message = data.get("message", "").strip()
    if not message:
        return JsonResponse({"error": "empty message"}, status=400)

    session_id = request.session.get("chat_session_id", str(uuid.uuid4()))
    request.session["chat_session_id"] = session_id

    session, _ = ChatSession.objects.get_or_create(
        session_id=session_id,
        defaults={"user": request.user}
    )

    ChatLog.objects.create(session=session, sender="USER", message=message)

    # Build recent history for context window management (Spec 4)
    history = [
        {"role": "user" if log.sender == "USER" else "assistant", "content": log.message}
        for log in session.messages.order_by("-timestamp")[:10][::-1]
    ]

    result = get_bot_response(message, history)

    ChatLog.objects.create(
        session=session, sender="BOT",
        message=result["reply"], escalated=result["escalated"]
    )

    return JsonResponse(result)