from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import SupportMessage

User = get_user_model()


@login_required
def support_chat_page(request):
    """Patient sees their own conversation with support staff."""
    if request.user.role != "PATIENT":
        return redirect("dashboard")

    messages = SupportMessage.objects.filter(patient=request.user).select_related("sender")
    return render(request, "support/chat.html", {"messages": messages})


@csrf_exempt
@login_required
def send_support_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    import json
    body = json.loads(request.body)
    text = body.get("message", "").strip()
    if not text:
        return JsonResponse({"error": "empty message"}, status=400)

    if request.user.role == "PATIENT":
        patient = request.user
    else:
        # Admin replying -- patient_id must be provided
        patient_id = body.get("patient_id")
        patient = User.objects.get(id=patient_id)

    SupportMessage.objects.create(patient=patient, sender=request.user, message=text)
    return JsonResponse({"status": "sent"})


@login_required
def get_support_messages(request, patient_id=None):
    """Polling endpoint -- returns messages as JSON so the chat updates without full reload."""
    if request.user.role == "PATIENT":
        patient = request.user
    else:
        patient = User.objects.get(id=patient_id)

    messages = SupportMessage.objects.filter(patient=patient).select_related("sender")
    data = [
        {
            "sender": m.sender.get_full_name() or m.sender.username,
            "is_staff": m.sender.role != "PATIENT",
            "message": m.message,
            "time": m.created_at.strftime("%I:%M %p"),
        }
        for m in messages
    ]
    return JsonResponse({"messages": data})


@login_required
def support_inbox(request):
    """Admin view -- list all patients who have sent support messages."""
    if request.user.role != "ADMIN":
        return redirect("dashboard")

    patient_ids = SupportMessage.objects.values_list("patient", flat=True).distinct()
    patients = User.objects.filter(id__in=patient_ids)
    return render(request, "support/inbox.html", {"patients": patients})


@login_required
def support_conversation(request, patient_id):
    if request.user.role != "ADMIN":
        return redirect("dashboard")

    patient = User.objects.get(id=patient_id)   # ← idhу irukkanum
    messages = SupportMessage.objects.filter(patient=patient).select_related("sender")
    SupportMessage.objects.filter(patient=patient).exclude(sender=request.user).update(is_read=True)

    return render(request, "support/conversation.html", {"patient": patient, "messages": messages})
    #                                    