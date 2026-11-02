
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),

    # Patient flow
    path("patient-login/", views.patient_login, name="patient_login"),
    path("patient-logout/", views.patient_logout, name="patient_logout"),
    path("patient-symptom/", views.patient_symptom, name="patient_symptom"),
    path("confirm-doctor/", views.confirm_doctor, name="confirm_doctor"),
    path("book-appointment/", views.book_appointment, name="book_appointment"),
    path("patient-dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("view-token/", views.view_token, name="view_token"),
    path("queue-position/", views.queue_position, name="queue_position"),
    path("appointment-history/", views.appointment_history, name="appointment_history"),

    # Doctor flow
    path("doctor-login/", views.doctor_login, name="doctor_login"),
    path("doctor-logout/", views.doctor_logout, name="doctor_logout"),
    path("doctor-dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("doctor-appointments/", views.doctor_appointments, name="doctor_appointments"),
    path("doctor-feedback/", views.doctor_feedback, name="doctor_feedback"),
    path(
        "complete-appointment/<int:appointment_id>/",
        views.complete_appointment,
        name="complete_appointment",
    ),

    # Symptom recommendation API
    path(
        "symptom-recommendation/",
        views.symptom_recommendation,
        name="symptom_recommendation",
    ),
]