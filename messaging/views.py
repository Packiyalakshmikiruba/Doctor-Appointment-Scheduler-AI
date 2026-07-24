from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Message

User = get_user_model()

@login_required
def contacts_list(request):
    """ஒரே பக்கத்தில் காண்டாக்ட் லிஸ்ட் மற்றும் சாட் பாக்ஸை ரெண்டர் செய்யும் வியூ"""
    current_user = request.user
    user_role = getattr(current_user, 'role', None)

    # ரோல் அடிப்படையிலான ஃபில்டரிங் லாஜிக்
    if user_role == 'ADMIN':
        users = User.objects.exclude(id=current_user.id)
    elif user_role in ['PATIENT', 'DOCTOR']:
        users = User.objects.filter(role='ADMIN').exclude(id=current_user.id)
    else:
        users = User.objects.none()

    return render(request, "messaging/chat.html", {"users": users}) # உங்கள் HTML கோப்பின் பெயர்


@csrf_exempt
@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    receiver_id = request.POST.get("receiver_id")
    body = request.POST.get("body", "").strip()
    uploaded_file = request.FILES.get("attachment")

    if not receiver_id:
        return JsonResponse({"error": "receiver_id required"}, status=400)

    if not body and not uploaded_file:
        return JsonResponse({"error": "message or attachment required"}, status=400)

    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "receiver not found"}, status=404)

    # Determine message type
    message_type = "TEXT"
    if uploaded_file:
        content_type = uploaded_file.content_type or ""
        if content_type.startswith("image/"):
            message_type = "IMAGE"
        elif content_type.startswith("audio/"):
            message_type = "VOICE"
        else:
            message_type = "FILE"

    msg = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        body=body,
        message_type=message_type,
        attachment=uploaded_file if uploaded_file else None,
    )

    # JS 'success' என்று செக் செய்வதால், இங்கும் 'success' என அனுப்புகிறோம்
    return JsonResponse({"status": "success", "message_id": msg.id})


@login_required
def get_messages_data(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by("created_at")

    # Read status update
    if hasattr(Message, 'is_read'):
        messages.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    data = []
    for m in messages:
        entry = {
            "sender_id": m.sender_id,
            "body": m.body,
            "message_type": m.message_type,
            "attachment_url": m.attachment.url if getattr(m, 'attachment', None) else None,
            "time": m.created_at.strftime("%I:%M %p"),
        }
        data.append(entry)

    return JsonResponse({
        "messages": data,
        "current_id": request.user.id,
        "opposite_username": other_user.get_full_name() or other_user.username,
    })