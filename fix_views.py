"""Script to update views.py with enhanced view functions."""
import re

with open('hospital/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize to LF for processing
content = content.replace('\r\n', '\n')

# 1. Replace queue_position function
old_qp_pattern = (
    r'def queue_position\(request\):.*?'
    r'return render\(\s*request,\s*"queue_position\.html",\s*\{\s*'
    r'"appointment": appointment,\s*'
    r'"position": position,\s*'
    r'\},\s*\)'
)

new_qp = '''def queue_position(request):
    patient_name = request.session.get("patient_name")
    if patient_name:
        appointment = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id").first()
    else:
        appointment = Appointment.objects.order_by("-appointment_date", "-id").first()

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
    )'''

match = re.search(old_qp_pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_qp + content[match.end():]
    print('queue_position replaced successfully')
else:
    print('ERROR: queue_position pattern not found')

# 2. Replace view_token function
old_vt_pattern = (
    r'def view_token\(request\):.*?'
    r'return render\(\s*request,\s*"view_token\.html",\s*\{"appointment": appointment\},\s*\)'
)

new_vt = '''def view_token(request):
    patient_name = request.session.get("patient_name")
    if patient_name:
        appointment = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id").first()
    else:
        appointment = Appointment.objects.order_by("-appointment_date", "-id").first()

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
    )'''

match = re.search(old_vt_pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_vt + content[match.end():]
    print('view_token replaced successfully')
else:
    print('ERROR: view_token pattern not found')

# 3. Replace appointment_history function
old_ah_pattern = (
    r'def appointment_history\(request\):.*?'
    r'return render\(\s*request,\s*"appointment_history\.html",\s*\{\s*'
    r'"appointments": appointments,\s*'
    r'"patient_name": patient_name,\s*'
    r'\},\s*\)'
)

new_ah = '''def appointment_history(request):
    patient_name = request.session.get("patient_name")
    if patient_name:
        appointments = Appointment.objects.filter(
            patient_name=patient_name
        ).order_by("-appointment_date", "-id")
    else:
        appointments = Appointment.objects.all().order_by(
            "-appointment_date", "-id"
        )

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
        status_choices = list(
            Appointment.objects.values_list("status", flat=True)
            .distinct()
            .order_by("status")
        )

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
    )'''

match = re.search(old_ah_pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_ah + content[match.end():]
    print('appointment_history replaced successfully')
else:
    print('ERROR: appointment_history pattern not found')

# Write back with CRLF
content = content.replace('\n', '\r\n')
with open('hospital/views.py', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print('\nAll views.py updates complete.')
