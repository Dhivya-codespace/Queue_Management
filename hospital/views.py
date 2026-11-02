from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from .models import Appointment, PatientFeedback
from .agents.supervisor import graph
from .agents.symptom_agent import symptom_agent


# =========================================================
# HOSPITAL CONFIGURATION
# =========================================================

HOSPITAL_LATITUDE = 11.0168
HOSPITAL_LONGITUDE = 76.9558

AVAILABLE_DOCTORS = ["Dr. Kumar", "Dr. Priya"]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    a = max(0.0, min(1.0, a))
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(radius * c, 2)


def get_location_details(post_data):
    raw_latitude = post_data.get("latitude", "").strip()
    raw_longitude = post_data.get("longitude", "").strip()

    if raw_latitude and raw_longitude:
        try:
            latitude = float(raw_latitude)
            longitude = float(raw_longitude)

            if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                distance = calculate_distance(
                    latitude,
                    longitude,
                    HOSPITAL_LATITUDE,
                    HOSPITAL_LONGITUDE,
                )

                # Local city transit estimate (~25 km/h) applies only for local distances (<= 100km).
                # For remote locations (> 100km), city driving estimates are not realistic.
                if distance <= 100:
                    estimated_minutes = max(1, round((distance / 25) * 60))
                else:
                    estimated_minutes = None

                if distance <= 5:
                    location_status = "Near Hospital (<= 5 km)"
                elif distance <= 50:
                    location_status = "In Service Region (5 - 50 km)"
                elif distance <= 100:
                    location_status = "Extended City Region (50 - 100 km)"
                else:
                    location_status = "Remote / Outside City Region" 

                location = (
                    f"Patient GPS: {latitude:.6f}, "
                    f"{longitude:.6f}"
                )

                map_url = (
                    "https://www.google.com/maps/dir/"
                    f"{latitude},{longitude}/"
                    f"{HOSPITAL_LATITUDE},{HOSPITAL_LONGITUDE}"
                )

                return {
                    "location": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "gps_captured": True,
                    "distance_km": distance,
                    "estimated_time": estimated_minutes,
                    "location_status": location_status,
                    "map_url": map_url,
                    "map_embed_url": (
                        "https://maps.google.com/maps?"
                        f"q={latitude},{longitude}&z=14&output=embed"
                    ),
                }

        except (ValueError, TypeError):
            pass

    return {
        "location": "Gandhipuram, Coimbatore (CareQueue Hospital)",
        "latitude": None,
        "longitude": None,
        "gps_captured": False,
        "distance_km": None,
        "estimated_time": None,
        "location_status": "GPS Coordinates Not Captured",
        "map_url": (
            "https://www.google.com/maps/search/"
            "?api=1&query=Gandhipuram%2C+Coimbatore"
        ),
        "map_embed_url": (
            "https://maps.google.com/maps?"
            "q=Gandhipuram%2C+Coimbatore&z=14&output=embed"
        ),
    }


def get_doctor_for_specialist(specialist):
    specialist = (specialist or "").lower()

    if any(k in specialist for k in ["cardio", "ortho", "dentist", "bone", "joint"]):
        return "Dr. Kumar"

    if any(k in specialist for k in ["derma", "skin", "eye", "ophthalm", "ent", "ear", "general"]):
        return "Dr. Priya"

    return "Dr. Kumar"


def is_doctor_authorized(request):
    """
    Check if the current user or session belongs to an authorized doctor or staff member.
    """
    doctor_name = request.session.get("doctor_name")
    if doctor_name:
        return True
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return True
    return False


def get_current_doctor_name(request):
    doctor_name = request.session.get("doctor_name")
    if not doctor_name and request.user.is_authenticated:
        doctor_name = request.user.get_full_name() or request.user.username
    return doctor_name or "Dr. Kumar"


def get_symptom_recommendation(symptoms):
    symptoms_lower = symptoms.lower()
    result = {}

    try:
        result = symptom_agent.analyze_symptoms(symptoms)

        if not isinstance(result, dict):
            result = {}

    except Exception as error:
        print("SYMPTOM AGENT ERROR:", error)

    doctor = (
        result.get("doctor")
        or result.get("recommended_doctor")
        or result.get("specialist")
        or result.get("department")
        or ""
    )

    recommendation = (
        result.get("recommendation")
        or result.get("message")
        or result.get("reason")
        or ""
    )

    risk_message = (
        result.get("risk_message")
        or result.get("warning")
        or ""
    )

    if not doctor:
        if any(word in symptoms_lower for word in [
            "chest pain", "heart pain", "heart"
        ]):
            doctor = "Cardiologist"
            recommendation = (
                "A medical professional should assess your symptoms. "
                "A Cardiologist may be appropriate."
            )

        elif any(word in symptoms_lower for word in [
            "skin", "rash", "itching", "acne"
        ]):
            doctor = "Dermatologist"
            recommendation = (
                "A Dermatologist may be appropriate for these symptoms."
            )

        elif any(word in symptoms_lower for word in [
            "eye", "eyes", "vision", "blurred"
        ]):
            doctor = "Ophthalmologist"
            recommendation = (
                "An Ophthalmologist may be appropriate for these symptoms."
            )

        elif any(word in symptoms_lower for word in [
            "ear", "nose", "throat"
        ]):
            doctor = "ENT Specialist"
            recommendation = (
                "An ENT Specialist may be appropriate for these symptoms."
            )

        elif any(word in symptoms_lower for word in [
            "tooth", "teeth", "gum", "dental"
        ]):
            doctor = "Dentist"
            recommendation = (
                "A Dentist may be appropriate for these symptoms."
            )

        elif any(word in symptoms_lower for word in [
            "bone", "joint", "knee", "back pain"
        ]):
            doctor = "Orthopedist"
            recommendation = (
                "An Orthopedist may be appropriate for these symptoms."
            )

        else:
            doctor = "General Physician"
            recommendation = (
                "A General Physician can assess your symptoms "
                "and advise you on the next steps."
            )

    emergency_phrases = [
        "severe chest pain",
        "difficulty breathing",
        "can't breathe",
        "cannot breathe",
        "unconscious",
        "fainting",
    ]

    if any(phrase in symptoms_lower for phrase in emergency_phrases):
        risk_message = (
            "These symptoms may require urgent medical attention. "
            "Please seek emergency medical care immediately."
        )

    return {
        "recommended_doctor": doctor,
        "recommendation": recommendation,
        "risk_message": risk_message,
    }


# =========================================================
# HOME, ABOUT, CONTACT
# =========================================================

def home(request):
    return render(request, "home.html")


def about_view(request):
    return render(request, "home.html", {"active_tab": "about"})


def contact_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or request.POST.get("contactName") or "").strip()
        email = (request.POST.get("email") or request.POST.get("contactEmail") or "").strip()
        message = (request.POST.get("message") or request.POST.get("contactMessage") or "").strip()

        # Handle JSON body if submitted via fetch
        if (not name or not email or not message) and request.content_type == "application/json":
            try:
                import json
                body_data = json.loads(request.body.decode("utf-8"))
                name = (body_data.get("name") or body_data.get("contactName") or "").strip()
                email = (body_data.get("email") or body_data.get("contactEmail") or "").strip()
                message = (body_data.get("message") or body_data.get("contactMessage") or "").strip()
            except Exception:
                pass

        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.content_type == "application/json"
            or request.headers.get("accept", "").find("application/json") != -1
        )

        if not name or not email or not message:
            error_msg = "Please fill in all the required fields (Name, Email, Message)."
            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=400)
            return render(request, "home.html", {"contact_error": error_msg, "active_tab": "contact"})

        if "@" not in email or "." not in email:
            error_msg = "Please enter a valid email address."
            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=400)
            return render(request, "home.html", {"contact_error": error_msg, "active_tab": "contact"})

        try:
            feedback = PatientFeedback.objects.create(
                name=name,
                email=email,
                message=message,
            )
            success_msg = f"Thank you, {name}! Your message has been received and saved successfully."
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": success_msg,
                    "feedback_id": feedback.id,
                })
            return render(request, "home.html", {"contact_success": success_msg, "active_tab": "contact"})

        except Exception as error:
            print("CONTACT SAVE ERROR:", error)
            error_msg = "An error occurred while saving your message. Please try again."
            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=500)
            return render(request, "home.html", {"contact_error": error_msg, "active_tab": "contact"})

    return render(request, "home.html", {"active_tab": "contact"})


# =========================================================
# PATIENT LOGIN & LOGOUT
# =========================================================

def patient_login(request):
    if request.method == "POST":
        patient_name = request.POST.get("patient_name", "").strip()
        password = request.POST.get("password", "").strip()

        if not patient_name or not password:
            return render(
                request,
                "patient_login.html",
                {"error": "Please enter your name and password."},
            )

        # Authenticate existing user or register new patient account with secure password hashing
        existing_user = User.objects.filter(username=patient_name).first()
        if existing_user:
            user = authenticate(request, username=patient_name, password=password)
            if not user:
                return render(
                    request,
                    "patient_login.html",
                    {"error": "Invalid password for this patient account."},
                )
            auth_login(request, user)
        else:
            # Create user account with hashed password
            user = User.objects.create_user(
                username=patient_name,
                password=password,
            )
            user.is_staff = False
            user.save()
            auth_login(request, user)

        request.session["patient_name"] = patient_name

        # Start a fresh symptom and appointment-selection flow.
        for key in (
            "patient_symptoms",
            "recommended_doctor",
            "selected_doctor",
        ):
            request.session.pop(key, None)

        request.session.modified = True

        print("Patient login successful:", patient_name)
        print("Redirecting to /patient-symptom/")

        return redirect("patient_symptom")

    return render(request, "patient_login.html")


def patient_logout(request):
    request.session.pop("patient_name", None)
    for key in ("patient_symptoms", "recommended_doctor", "selected_doctor"):
        request.session.pop(key, None)
    auth_logout(request)
    return redirect("home")


# =========================================================
# PATIENT SYMPTOM PAGE
# =========================================================

def patient_symptom(request):
    patient_name = request.session.get("patient_name", "")

    if not patient_name:
        return redirect("patient_login")

    if request.method == "POST":
        symptoms = request.POST.get("symptoms", "").strip()

        if not symptoms:
            return render(
                request,
                "patient_symptom.html",
                {
                    "patient_name": patient_name,
                    "error": "Please enter your symptoms.",
                },
            )

        result = get_symptom_recommendation(symptoms)

        recommended_doctor = result["recommended_doctor"]

        request.session["patient_symptoms"] = symptoms
        request.session["recommended_doctor"] = recommended_doctor

        # The patient must confirm a doctor again after new analysis.
        request.session.pop("selected_doctor", None)

        request.session.modified = True

        return render(
            request,
            "patient_symptom.html",
            {
                "patient_name": patient_name,
                "symptoms": symptoms,
                "recommended_doctor": recommended_doctor,
                "recommendation": result["recommendation"],
                "risk_message": result["risk_message"],
                "show_recommendation": True,
            },
        )

    # A GET request always displays the symptom page.
    return render(
        request,
        "patient_symptom.html",
        {
            "patient_name": patient_name,
            "symptoms": request.session.get("patient_symptoms", ""),
        },
    )


# =========================================================
# CONFIRM DOCTOR
# =========================================================

def confirm_doctor(request):
    if request.method != "POST":
        return redirect("patient_symptom")

    patient_name = request.session.get("patient_name", "")
    symptoms = request.session.get("patient_symptoms", "")
    recommended_doctor = request.session.get(
        "recommended_doctor", ""
    )

    if not patient_name:
        return redirect("patient_login")

    if not symptoms or not recommended_doctor:
        return redirect("patient_symptom")

    selected_doctor = get_doctor_for_specialist(recommended_doctor)

    request.session["selected_doctor"] = selected_doctor
    request.session.modified = True

    print("Doctor recommendation:", recommended_doctor)
    print("Selected available doctor:", selected_doctor)

    # Booking opens only after doctor confirmation.
    return redirect("book_appointment")


# =========================================================
# SYMPTOM RECOMMENDATION API
# =========================================================

def symptom_recommendation(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    symptoms = request.POST.get("symptoms", "").strip()

    if not symptoms:
        return JsonResponse(
            {"error": "Please enter your symptoms."},
            status=400,
        )

    try:
        return JsonResponse(get_symptom_recommendation(symptoms))

    except Exception as error:
        print("SYMPTOM API ERROR:", error)

        return JsonResponse(
            {"error": "Unable to analyze symptoms right now."},
            status=500,
        )


# =========================================================
# DOCTOR LOGIN & LOGOUT
# =========================================================

def doctor_login(request):
    if request.method == "POST":
        doctor_name = request.POST.get("doctor_name", "").strip()
        password = request.POST.get("password", "")

        # Authenticate via Django Auth User
        user = authenticate(request, username=doctor_name, password=password)
        if user and (user.is_staff or user.is_superuser):
            auth_login(request, user)
            request.session["doctor_name"] = doctor_name
            request.session.modified = True
            return redirect("doctor_dashboard")

        # Support default doctor logins if accounts are being created/synced
        if (doctor_name in AVAILABLE_DOCTORS or doctor_name in ["Dr. Kumar", "Dr. Priya"]) and password == "1234":
            staff_user, _ = User.objects.get_or_create(username=doctor_name, defaults={"is_staff": True})
            staff_user.is_staff = True
            staff_user.set_password(password)
            staff_user.save()
            user = authenticate(request, username=doctor_name, password=password)
            if user:
                auth_login(request, user)
            request.session["doctor_name"] = doctor_name
            request.session.modified = True
            return redirect("doctor_dashboard")

        return render(
            request,
            "doctor_login.html",
            {"error": "Invalid doctor name or password."},
        )

    return render(request, "doctor_login.html")


def doctor_logout(request):
    request.session.pop("doctor_name", None)
    auth_logout(request)
    return redirect("home")


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

def doctor_dashboard(request):
    if not is_doctor_authorized(request):
        return redirect("doctor_login")

    doctor_name = get_current_doctor_name(request)

    # Doctor views their own patients, superuser views all
    if request.user.is_authenticated and request.user.is_superuser:
        doctor_qs = Appointment.objects.all()
    else:
        doctor_qs = Appointment.objects.filter(doctor=doctor_name)

    total_patients = doctor_qs.count()
    pending_patients = doctor_qs.filter(status="Pending").count()
    completed_patients = doctor_qs.filter(status="Completed").count()
    high_priority = doctor_qs.filter(priority="High").count()
    feedback_count = PatientFeedback.objects.count()

    return render(
        request,
        "doctor_dashboard.html",
        {
            "doctor_name": doctor_name,
            "total_patients": total_patients,
            "pending_patients": pending_patients,
            "completed_patients": completed_patients,
            "high_priority": high_priority,
            "feedback_count": feedback_count,
        },
    )


# =========================================================
# PATIENT DASHBOARD
# =========================================================

def patient_dashboard(request):
    patient_name = request.session.get("patient_name")
    if patient_name:
        appointment = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id").first()
    else:
        appointment = Appointment.objects.order_by("-appointment_date", "-id").first()

    return render(
        request,
        "patient_dashboard.html",
        {
            "appointment": appointment,
            "patient_name": patient_name,
        },
    )


# =========================================================
# VIEW TOKEN
# =========================================================

def view_token(request):
    patient_name = request.session.get("patient_name") or (
        request.user.username if request.user.is_authenticated and not request.user.is_staff else None
    )
    if patient_name:
        appointment = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id").first()
    else:
        appointment = None

    # Calculate queue position for the token page
    queue_position_val = None
    estimated_wait = None
    if appointment and appointment.status == "Pending":
        qbase = Appointment.objects.filter(
            status="Pending",
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
        )
        if appointment.priority == "High":
            queue_position_val = qbase.filter(priority="High", id__lte=appointment.id).count()
        elif appointment.priority == "Medium":
            queue_position_val = qbase.filter(priority="High").count() + qbase.filter(priority="Medium", id__lte=appointment.id).count()
        else:
            queue_position_val = qbase.filter(priority="High").count() + qbase.filter(priority="Medium").count() + qbase.filter(priority="Low", id__lte=appointment.id).count()
        patients_ahead = max(0, queue_position_val - 1)
        estimated_wait = patients_ahead * 10 if patients_ahead > 0 else 0

    return render(
        request,
        "view_token.html",
        {
            "appointment": appointment,
            "patient_name": patient_name,
            "queue_position": queue_position_val,
            "estimated_wait": estimated_wait,
        },
    )


# =========================================================
# BOOK APPOINTMENT
# =========================================================

def book_appointment(request):
    patient_name = request.session.get("patient_name", "")
    symptoms = request.session.get("patient_symptoms", "")
    recommended_doctor = request.session.get(
        "recommended_doctor", ""
    )
    selected_doctor = request.session.get("selected_doctor", "")

    if not patient_name:
        return redirect("patient_login")

    # Require symptom analysis and doctor confirmation.
    if (
        not symptoms
        or not recommended_doctor
        or not selected_doctor
    ):
        return redirect("patient_symptom")

    if request.method == "GET":
        return render(
            request,
            "book_appointment.html",
            {
                "patient_name": patient_name,
                "symptoms": symptoms,
                "recommended_doctor": recommended_doctor,
                "selected_doctor": selected_doctor,
            },
        )

    # READ FORM DATA
    form_patient_name = (
        request.POST.get("patient_name", patient_name).strip()
        or patient_name
    )

    mobile_number = (
        request.POST.get("mobile_number", "")
        or request.POST.get("mobile", "")
    ).strip()

    raw_doctor = request.POST.get("doctor", "").strip()

    if raw_doctor in AVAILABLE_DOCTORS:
        doctor = raw_doctor
    elif selected_doctor in AVAILABLE_DOCTORS:
        doctor = selected_doctor
    else:
        doctor = "Dr. Kumar"

    appointment_date_input = request.POST.get(
        "appointment_date", ""
    ).strip()

    appointment_time_input = request.POST.get(
        "appointment_time", ""
    ).strip()

    symptoms = (
        request.POST.get("symptoms", symptoms).strip()
        or symptoms
    )

    # PATIENT LOCATION
    location_data = get_location_details(request.POST)

    location = location_data["location"]
    latitude = location_data["latitude"]
    longitude = location_data["longitude"]
    gps_captured = location_data["gps_captured"]
    distance_km = location_data["distance_km"]
    estimated_time = location_data["estimated_time"]
    location_status = location_data["location_status"]
    map_url = location_data["map_url"]
    map_embed_url = location_data["map_embed_url"]

    agent_distance = (
        distance_km if distance_km is not None else 0
    )

    agent_estimated_time = (
        estimated_time if estimated_time is not None else 0
    )

    # VALIDATE MOBILE NUMBER
    if len(mobile_number) != 10 or not mobile_number.isdigit():
        return render(
            request,
            "book_appointment.html",
            {
                "error": "Please enter a valid 10-digit mobile number.",
                "patient_name": form_patient_name,
                "symptoms": symptoms,
                "recommended_doctor": recommended_doctor,
                "selected_doctor": doctor,
            },
        )

    # VALIDATE DATE
    try:
        appointment_date = datetime.strptime(
            appointment_date_input, "%Y-%m-%d"
        ).date()

        if appointment_date < datetime.today().date():
            raise ValueError("Past dates are not allowed.")

    except (ValueError, TypeError):
        return render(
            request,
            "book_appointment.html",
            {
                "error": "Please choose a valid future appointment date.",
                "patient_name": form_patient_name,
                "symptoms": symptoms,
                "recommended_doctor": recommended_doctor,
                "selected_doctor": doctor,
            },
        )

    # VALIDATE TIME
    appointment_time = None

    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            appointment_time = datetime.strptime(
                appointment_time_input, time_format
            ).time()
            break
        except (ValueError, TypeError):
            continue

    if appointment_time is None:
        return render(
            request,
            "book_appointment.html",
            {
                "error": "Please choose a valid appointment time.",
                "patient_name": form_patient_name,
                "symptoms": symptoms,
                "recommended_doctor": recommended_doctor,
                "selected_doctor": doctor,
            },
        )

    # GENERATE TOKEN AND CREATE APPOINTMENT (ATOMIC & CONCURRENCY-SAFE)
    with transaction.atomic():
        last_appointment = (
            Appointment.objects.select_for_update()
            .filter(
                doctor=doctor,
                appointment_date=appointment_date,
            )
            .order_by("-token_number")
            .first()
        )

        token_number = (
            last_appointment.token_number + 1
            if last_appointment
            else 1
        )

        print("NEW TOKEN GENERATED")
        print("Patient:", form_patient_name)
        print("Doctor:", doctor)
        print("Date:", appointment_date)
        print("Token:", token_number)
        print("GPS captured:", gps_captured)
        print("Location:", location)
        print("Distance:", distance_km)

        # CREATE APPOINTMENT IN DATABASE
        appointment = Appointment.objects.create(
            patient_name=form_patient_name,
            mobile_number=mobile_number,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            symptoms=symptoms,
            token_number=token_number,
            latitude=latitude,
            longitude=longitude,
            status="Pending",
        )

    # Persist patient session
    request.session["patient_name"] = form_patient_name
    request.session["last_appointment_id"] = appointment.id
    request.session.modified = True

    # CURRENT SERVING TOKEN
    current_appointment = (
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status="Pending",
        )
        .order_by("token_number")
        .first()
    )

    current_token = (
        current_appointment.token_number
        if current_appointment
        else token_number
    )

    # AI AGENT WORKFLOW
    agent_data = {
        "patient_name": form_patient_name,
        "doctor_name": doctor,
        "appointment_time": appointment_time_input,
        "symptoms": symptoms,
        "booking_status": "",
        "doctor_available": False,
        "location": location,
        "distance_km": agent_distance,
        "estimated_time": agent_estimated_time,
        "location_status": location_status,
        "risk_score": 0,
        "priority": "",
        "token_number": token_number,
        "current_token": current_token,
        "notification_message": "",
        "patients_before": 0,
        "estimated_wait_time": 0,
    }

    try:
        result = graph.invoke(agent_data)

        if not isinstance(result, dict):
            result = {}

    except Exception as error:
        print("AI AGENT ERROR:", error)
        result = {}

    print("AI AGENT RESULT:", result)

    # SAVE AI VALUES
    appointment.risk_score = result.get("risk_score", 0)
    appointment.priority = result.get("priority", "Low") or "Low"
    appointment.token_number = token_number
    appointment.save()

    patients_before = result.get("patients_before", 0)
    estimated_wait_time = result.get("estimated_wait_time", 0)

    doctor_available = doctor in AVAILABLE_DOCTORS

    # SUCCESS PAGE
    return render(
        request,
        "appointment_success.html",
        {
            "appointment_id": appointment.id,
            "patient_name": form_patient_name,
            "mobile_number": mobile_number,
            "doctor": doctor,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time.strftime("%I:%M %p"),
            "doctor_available": doctor_available,
            "risk_score": appointment.risk_score,
            "priority": appointment.priority,
            "token_number": appointment.token_number,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "patient_latitude": latitude,
            "patient_longitude": longitude,
            "gps_captured": gps_captured,
            "distance_km": distance_km,
            "estimated_time": estimated_time,
            "location_status": location_status,
            "map_url": map_url,
            "map_embed_url": map_embed_url,
            "hospital_latitude": HOSPITAL_LATITUDE,
            "hospital_longitude": HOSPITAL_LONGITUDE,
            "patients_before": patients_before,
            "estimated_wait_time": estimated_wait_time,
            "notification_message": result.get(
                "notification_message", ""
            ),
        },
    )


# =========================================================
# QUEUE POSITION
# =========================================================

def queue_position(request):
    patient_name = request.session.get("patient_name") or (
        request.user.username if request.user.is_authenticated and not request.user.is_staff else None
    )
    if patient_name:
        appointment = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id").first()
    else:
        appointment = None

    if not appointment:
        return render(
            request,
            "queue_position.html",
            {
                "appointment": None,
                "position": 0,
                "patients_ahead": 0,
                "estimated_wait_time": None,
                "queue_steps": [],
                "active_step_index": -1,
                "patient_name": patient_name,
            },
        )

    base = Appointment.objects.filter(
        status="Pending",
        doctor=appointment.doctor,
        appointment_date=appointment.appointment_date,
    )

    if appointment.priority == "High":
        position = base.filter(
            priority="High",
            id__lte=appointment.id,
        ).count()

    elif appointment.priority == "Medium":
        high = base.filter(priority="High").count()

        medium = base.filter(
            priority="Medium",
            id__lte=appointment.id,
        ).count()

        position = high + medium

    else:
        high = base.filter(priority="High").count()
        medium = base.filter(priority="Medium").count()

        low = base.filter(
            priority="Low",
            id__lte=appointment.id,
        ).count()

        position = high + medium + low

    # Calculate patients ahead (position - 1, minimum 0)
    patients_ahead = max(0, position - 1) if appointment.status == "Pending" else 0

    # Estimate waiting time: ~10 minutes per patient ahead (only if Pending)
    if appointment.status == "Pending" and patients_ahead > 0:
        estimated_wait_time = patients_ahead * 10
    elif appointment.status == "Pending" and patients_ahead == 0:
        estimated_wait_time = 0
    else:
        estimated_wait_time = None

    # Queue progress steps matching the project actual status values
    queue_steps = [
        {"label": "Registered", "status": "Registered"},
        {"label": "Waiting", "status": "Pending"},
        {"label": "In Consultation", "status": "In Progress"},
        {"label": "Completed", "status": "Completed"},
    ]

    # Determine the active step index based on appointment status
    status_lower = (appointment.status or "").lower()
    active_step_index = 0
    if status_lower == "pending":
        active_step_index = 1
    elif status_lower in ("in progress", "in consultation", "consulting"):
        active_step_index = 2
    elif status_lower == "completed":
        active_step_index = 3

    return render(
        request,
        "queue_position.html",
        {
            "appointment": appointment,
            "position": position,
            "patients_ahead": patients_ahead,
            "estimated_wait_time": estimated_wait_time,
            "queue_steps": queue_steps,
            "active_step_index": active_step_index,
            "patient_name": patient_name,
        },
    )


# =========================================================
# APPOINTMENT HISTORY
# =========================================================

def appointment_history(request):
    patient_name = request.session.get("patient_name") or (
        request.user.username if request.user.is_authenticated and not request.user.is_staff else None
    )
    if patient_name:
        appointments = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id")
    else:
        appointments = Appointment.objects.none()

    # Get search and filter parameters
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        from django.db.models import Q
        appointments = appointments.filter(
            Q(doctor__icontains=search_query) | Q(token_number__icontains=search_query)
        )

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Get distinct status values for filter dropdown
    if patient_name:
        status_choices = list(
            Appointment.objects.filter(patient_name=patient_name)
            .values_list("status", flat=True)
            .distinct()
            .order_by("status")
        )
    else:
        status_choices = []

    return render(
        request,
        "appointment_history.html",
        {
            "appointments": appointments,
            "patient_name": patient_name,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_choices": status_choices,
        },
    )


# =========================================================
# DOCTOR APPOINTMENTS
# =========================================================

def doctor_appointments(request):
    if not is_doctor_authorized(request):
        return redirect("doctor_login")

    doctor_name = get_current_doctor_name(request)

    if request.user.is_authenticated and request.user.is_superuser:
        appointments = Appointment.objects.all().order_by(
            "status", "token_number"
        )
    else:
        appointments = Appointment.objects.filter(
            doctor=doctor_name
        ).order_by("status", "token_number")

    return render(
        request,
        "doctor_appointments.html",
        {
            "doctor_name": doctor_name,
            "appointments": appointments,
        },
    )


# =========================================================
# COMPLETE APPOINTMENT
# =========================================================

def complete_appointment(request, appointment_id):
    if not is_doctor_authorized(request):
        return redirect("doctor_login")

    doctor_name = get_current_doctor_name(request)
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
    )

    # Permission check: superuser or assigned doctor
    if request.user.is_authenticated and request.user.is_superuser:
        pass
    elif appointment.doctor != doctor_name:
        return redirect("doctor_appointments")

    appointment.status = "Completed"
    appointment.save()

    return redirect("doctor_appointments")


# =========================================================
# DOCTOR FEEDBACK MANAGEMENT
# =========================================================

def doctor_feedback(request):
    if not is_doctor_authorized(request):
        return redirect("doctor_login")

    doctor_name = get_current_doctor_name(request)
    feedback_list = PatientFeedback.objects.all().order_by("-created_at")

    return render(
        request,
        "doctor_feedback.html",
        {
            "doctor_name": doctor_name,
            "feedback_list": feedback_list,
        },
    )
