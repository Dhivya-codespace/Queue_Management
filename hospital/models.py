from django.db import models


class Appointment(models.Model):
    patient_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    doctor = models.CharField(max_length=100)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField()
    risk_score = models.IntegerField(default=0)
    priority = models.CharField(max_length=20, default="")
    token_number = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="Pending")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # SMS queue notification tracking
    sms_notification_sent = models.BooleanField(default=False)
    sms_notification_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-appointment_date", "-token_number", "-id"]

    def __str__(self):
        return f"{self.patient_name} - {self.doctor} (Token #{self.token_number})"


class PatientFeedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Patient Feedback"
        verbose_name_plural = "Patient Feedback"
        ordering = ["-created_at"]

    def __str__(self):
        created_str = self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else ""
        return f"{self.name} ({self.email}) - {created_str}"