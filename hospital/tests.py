from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from hospital.models import Appointment, PatientFeedback


class CareQueueComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Initialize test doctor accounts
        self.doctor_kumar = User.objects.create_user(
            username="Dr. Kumar",
            password="1234",
            is_staff=True
        )
        self.doctor_priya = User.objects.create_user(
            username="Dr. Priya",
            password="1234",
            is_staff=True
        )
        self.admin_user = User.objects.create_superuser(
            username="testadmin",
            password="adminpassword",
            email="admin@test.com"
        )

    # -------------------------------------------------------------------------
    # 1. Navigation & Basic Routes
    # -------------------------------------------------------------------------
    def test_public_routes_resolve_and_render(self):
        """Test home, about, and contact routes resolve and render successfully."""
        routes = [
            ("home", 200),
            ("about", 200),
            ("contact", 200),
            ("patient_login", 200),
            ("doctor_login", 200),
        ]
        for name, expected_status in routes:
            response = self.client.get(reverse(name))
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Route {name} failed with status {response.status_code}"
            )

    # -------------------------------------------------------------------------
    # 2. Patient Login Workflow
    # -------------------------------------------------------------------------
    def test_patient_login_new_user_creates_hashed_account(self):
        """New patient login should create an account with hashed password and set session."""
        response = self.client.post(reverse("patient_login"), {
            "patient_name": "Ramesh",
            "password": "securepassword123"
        })
        self.assertRedirects(response, reverse("patient_symptom"))
        self.assertEqual(self.client.session.get("patient_name"), "Ramesh")

        # Verify user was created with hashed password, not plain text
        user = User.objects.get(username="Ramesh")
        self.assertTrue(user.check_password("securepassword123"))
        self.assertNotEqual(user.password, "securepassword123")

    def test_patient_login_invalid_password_rejected(self):
        """Existing patient account with wrong password should be rejected."""
        # Create existing patient
        User.objects.create_user(username="Sita", password="correct_password")

        response = self.client.post(reverse("patient_login"), {
            "patient_name": "Sita",
            "password": "wrong_password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid password")
        self.assertIsNone(self.client.session.get("patient_name"))

    def test_patient_login_empty_fields_rejected(self):
        """Empty patient credentials should return an error."""
        response = self.client.post(reverse("patient_login"), {
            "patient_name": "",
            "password": ""
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your name and password")

    # -------------------------------------------------------------------------
    # 3. Patient Symptoms & Doctor Confirmation Flow
    # -------------------------------------------------------------------------
    def test_patient_symptom_workflow(self):
        """Patient enters symptoms, gets recommendation, confirms doctor."""
        # Must be logged in to view symptoms
        response = self.client.get(reverse("patient_symptom"))
        self.assertRedirects(response, reverse("patient_login"))

        # Log in
        self.client.post(reverse("patient_login"), {
            "patient_name": "Ramesh",
            "password": "password123"
        })

        # Submit chest pain symptoms
        response = self.client.post(reverse("patient_symptom"), {
            "symptoms": "severe chest pain and palpitations"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cardiologist")
        self.assertEqual(self.client.session.get("recommended_doctor"), "Cardiologist")

        # Confirm doctor
        confirm_resp = self.client.post(reverse("confirm_doctor"))
        self.assertRedirects(confirm_resp, reverse("book_appointment"))
        self.assertEqual(self.client.session.get("selected_doctor"), "Dr. Kumar")

    # -------------------------------------------------------------------------
    # 4. Appointment Booking, GPS Coordinates, & Token Generation
    # -------------------------------------------------------------------------
    def test_appointment_booking_past_date_rejected(self):
        """Booking with past date should be rejected with an error message."""
        session = self.client.session
        session["patient_name"] = "Ramesh"
        session["patient_symptoms"] = "Headache"
        session["recommended_doctor"] = "General Physician"
        session["selected_doctor"] = "Dr. Kumar"
        session.save()

        past_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        response = self.client.post(reverse("book_appointment"), {
            "patient_name": "Ramesh",
            "mobile_number": "9876543210",
            "doctor": "Dr. Kumar",
            "appointment_date": past_date,
            "appointment_time": "10:00 AM",
            "symptoms": "Headache",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please choose a valid future appointment date")
        self.assertEqual(Appointment.objects.filter(patient_name="Ramesh").count(), 0)

    def test_appointment_booking_invalid_mobile_rejected(self):
        """Invalid mobile number (not 10 digits) should be rejected."""
        session = self.client.session
        session["patient_name"] = "Ramesh"
        session["patient_symptoms"] = "Fever"
        session["recommended_doctor"] = "General Physician"
        session["selected_doctor"] = "Dr. Kumar"
        session.save()

        future_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = self.client.post(reverse("book_appointment"), {
            "patient_name": "Ramesh",
            "mobile_number": "123",  # invalid
            "doctor": "Dr. Kumar",
            "appointment_date": future_date,
            "appointment_time": "10:00 AM",
            "symptoms": "Fever",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid 10-digit mobile number")
        self.assertEqual(Appointment.objects.filter(patient_name="Ramesh").count(), 0)

    def test_successful_appointment_booking_with_gps_persistence(self):
        """Valid appointment booking saves to database with GPS coordinates and assigns token."""
        session = self.client.session
        session["patient_name"] = "Kavitha"
        session["patient_symptoms"] = "Skin rash and itching"
        session["recommended_doctor"] = "Dermatologist"
        session["selected_doctor"] = "Dr. Priya"
        session.save()

        future_date = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        post_data = {
            "patient_name": "Kavitha",
            "mobile_number": "9876543210",
            "doctor": "Dr. Priya",
            "appointment_date": future_date,
            "appointment_time": "11:00 AM",
            "symptoms": "Skin rash and itching",
            "latitude": "11.025000",
            "longitude": "76.965000",
        }

        response = self.client.post(reverse("book_appointment"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appointment Booked Successfully")

        # Verify saved in database
        saved_appt = Appointment.objects.filter(patient_name="Kavitha").last()
        self.assertIsNotNone(saved_appt)
        self.assertEqual(saved_appt.doctor, "Dr. Priya")
        self.assertEqual(saved_appt.status, "Pending")
        self.assertEqual(saved_appt.mobile_number, "9876543210")
        self.assertAlmostEqual(saved_appt.latitude, 11.025, places=3)
        self.assertAlmostEqual(saved_appt.longitude, 76.965, places=3)
        self.assertGreaterEqual(saved_appt.token_number, 1)

        # Verify template receives coordinates for Leaflet rendering
        self.assertIn("patient_latitude", response.context)
        self.assertIn("patient_longitude", response.context)
        self.assertEqual(response.context["patient_latitude"], 11.025)
        self.assertEqual(response.context["patient_longitude"], 76.965)

    def test_token_number_increments_for_same_doctor_and_date(self):
        """Tokens should increment sequentially for the same doctor and appointment date."""
        target_date = date.today() + timedelta(days=3)
        date_str = target_date.strftime("%Y-%m-%d")

        for idx, name in enumerate(["Patient1", "Patient2", "Patient3"], start=1):
            session = self.client.session
            session["patient_name"] = name
            session["patient_symptoms"] = "Checkup"
            session["recommended_doctor"] = "General Physician"
            session["selected_doctor"] = "Dr. Kumar"
            session.save()

            resp = self.client.post(reverse("book_appointment"), {
                "patient_name": name,
                "mobile_number": "9123456780",
                "doctor": "Dr. Kumar",
                "appointment_date": date_str,
                "appointment_time": "10:00 AM",
                "symptoms": "Checkup",
            })
            self.assertEqual(resp.status_code, 200)
            appt = Appointment.objects.get(patient_name=name, appointment_date=target_date)
            self.assertEqual(appt.token_number, idx)

    # -------------------------------------------------------------------------
    # 5. Patient Feedback Persistence & Django Admin Integration
    # -------------------------------------------------------------------------
    def test_contact_feedback_saves_to_database(self):
        """Contact message submission must save to the PatientFeedback model in database."""
        initial_count = PatientFeedback.objects.count()
        response = self.client.post(
            reverse("contact"),
            {
                "name": "Anand Sharma",
                "email": "anand@example.com",
                "message": "The queue display at reception is very helpful. Thank you!"
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(PatientFeedback.objects.count(), initial_count + 1)

        saved_feedback = PatientFeedback.objects.filter(email="anand@example.com").first()
        self.assertIsNotNone(saved_feedback)
        self.assertEqual(saved_feedback.name, "Anand Sharma")
        self.assertIn("queue display", saved_feedback.message)

    def test_contact_feedback_validation_failure(self):
        """Contact form with missing fields returns 400 error and does not save."""
        initial_count = PatientFeedback.objects.count()
        response = self.client.post(
            reverse("contact"),
            {
                "name": "",
                "email": "invalid_email",
                "message": ""
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(PatientFeedback.objects.count(), initial_count)

    def test_models_registered_in_django_admin(self):
        """Appointment and PatientFeedback must both be registered in admin.site."""
        self.assertIn(Appointment, site._registry)
        self.assertIn(PatientFeedback, site._registry)

    def test_django_admin_access_for_superuser(self):
        """Superuser should be able to view patient feedback in Django admin."""
        # Create test feedback
        PatientFeedback.objects.create(
            name="John Doe",
            email="john@example.com",
            message="Test admin visibility"
        )
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.get("/admin/hospital/patientfeedback/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "john@example.com")

    # -------------------------------------------------------------------------
    # 6. Doctor Login, Authorization, Dashboard, & Appointment Status
    # -------------------------------------------------------------------------
    def test_unauthenticated_doctor_dashboard_redirects_to_login(self):
        """Unauthenticated visitor trying to access doctor dashboard is redirected."""
        response = self.client.get(reverse("doctor_dashboard"))
        self.assertRedirects(response, reverse("doctor_login"))

    def test_doctor_login_success_and_appointment_completion(self):
        """Doctor logs in, sees their own appointments, and can complete them."""
        # Create appointment for Dr. Kumar and one for Dr. Priya
        future_date = date.today() + timedelta(days=1)
        appt_kumar = Appointment.objects.create(
            patient_name="Patient Kumar",
            mobile_number="9876543210",
            doctor="Dr. Kumar",
            appointment_date=future_date,
            appointment_time="09:00",
            symptoms="Chest pain",
            status="Pending",
            token_number=1
        )
        appt_priya = Appointment.objects.create(
            patient_name="Patient Priya",
            mobile_number="9876543211",
            doctor="Dr. Priya",
            appointment_date=future_date,
            appointment_time="10:00",
            symptoms="Skin rash",
            status="Pending",
            token_number=1
        )

        # Log in as Dr. Kumar
        login_resp = self.client.post(reverse("doctor_login"), {
            "doctor_name": "Dr. Kumar",
            "password": "1234"
        })
        self.assertRedirects(login_resp, reverse("doctor_dashboard"))

        # Access doctor dashboard
        dash_resp = self.client.get(reverse("doctor_dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "Dr. Kumar")

        # Access doctor appointments list - should contain Patient Kumar, NOT Patient Priya
        appts_resp = self.client.get(reverse("doctor_appointments"))
        self.assertEqual(appts_resp.status_code, 200)
        self.assertContains(appts_resp, "Patient Kumar")
        self.assertNotContains(appts_resp, "Patient Priya")

        # Complete Dr. Kumar's appointment
        complete_resp = self.client.get(
            reverse("complete_appointment", args=[appt_kumar.id])
        )
        self.assertRedirects(complete_resp, reverse("doctor_appointments"))
        appt_kumar.refresh_from_db()
        self.assertEqual(appt_kumar.status, "Completed")
