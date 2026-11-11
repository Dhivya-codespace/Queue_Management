from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('hospital', '0005_patientfeedback_alter_appointment_options_and_more'),
    ]

    # No-op: sms_notification_sent and sms_notification_sent_at are already
    # added by 0006_appointment_sms_notification_sent_and_more. Keeping this
    # empty preserves compatibility with both existing and fresh databases.
    operations = []
