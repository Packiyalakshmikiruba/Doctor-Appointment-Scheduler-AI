"""
chatbot/views.py
Django views for the chat widget and its API endpoint.
"""

import json
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .agent import get_agent_response
from .tools import symptom_to_department, search_doctor

_SESSION_HISTORY = {}


def chat_widget(request):
    return render(request, "chatbot/chat_widget.html")


@csrf_exempt
def upload_medical_file(request):
    """
    Accepts an old medical report/file image from a new patient, extracts
    its text via OCR, and suggests a department + doctor to refer them to --
    based only on what's already written in the document. This is
    administrative routing, not a diagnosis: it never adds a medical
    opinion beyond pointing to the right department.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    image_file = request.FILES.get("file")
    if not image_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_file)
        extracted_text = pytesseract.image_to_string(img).strip()
    except Exception as e:
        return JsonResponse(
            {"error": f"Could not read the image: {e}"}, status=500
        )

    if not extracted_text:
        return JsonResponse({
            "extracted_text": "",
            "response": (
                "I couldn't read any text from that image. Could you upload "
                "a clearer photo, or tell me what the report says?"
            ),
        })

    department = symptom_to_department.func(extracted_text)
    doctors = search_doctor.func(department)

    reply = (
        f"From the uploaded file, this looks related to: {department}.\n\n"
        f"{doctors}\n\n"
        f"This is a suggested referral based on the document only -- please "
        f"have the doctor review the full file at the consultation. "
        f"To book, visit the appointment page and select one of these doctors."
    )

    return JsonResponse({
        "extracted_text": extracted_text[:1000],
        "response": reply,
    })


@csrf_exempt
def chat_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = body.get("message", "").strip()

    if not user_message:
        return JsonResponse({"error": "message required"}, status=400)

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    current_user = request.user.id if request.user.is_authenticated else "guest"

    if request.session.get("chat_user") != current_user:
        _SESSION_HISTORY[session_key] = []
        request.session["chat_user"] = current_user

    history = _SESSION_HISTORY.get(session_key, [])

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
        # Fixed: use keyword arguments -- never rely on positional order
        # for functions with multiple optional params of similar type.
        reply, history = get_agent_response(
            user_message,
            history=history,
            patient_id=patient_id,
            doctor_id=doctor_id,
            user_role=user_role,
            session_key=session_key,
        )

        _SESSION_HISTORY[session_key] = history

        return JsonResponse({"response": reply})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"response": f"Error: {str(e)}"}, status=500)