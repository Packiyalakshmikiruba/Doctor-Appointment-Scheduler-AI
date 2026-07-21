from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

MESSAGES = []
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

    return render(request, "messaging/contacts_list.html", {"users": users})

@csrf_exempt
@login_required
def send_message(request):
    if request.method == "POST":
        body = request.POST.get("body")
        receiver_id = request.POST.get("receiver_id")
        
        if not body or not receiver_id:
            return JsonResponse({"status": "error"}, status=400)
            
        MESSAGES.append({
            "sender_id": request.user.id,
            "receiver_id": int(receiver_id),
            "body": body,
            "time": datetime.now().strftime("%H:%M")
        })
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

@login_required
def get_messages(request, user_id):
    target_id = int(user_id)
    current_id = request.user.id
    
    chat = [m for m in MESSAGES if (m["sender_id"] == current_id and m["receiver_id"] == target_id) or 
                                   (m["sender_id"] == target_id and m["receiver_id"] == current_id)]
    
    return JsonResponse({"messages": chat, "current_id": current_id})