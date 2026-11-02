from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('hospital', '0005_patientfeedback_alter_appointment_options_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='appointment',
            name='sms_notification_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='appointment',
            name='sms_notification_sent_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
