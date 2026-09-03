from clinic_sms.appointment_campaign import AppointmentNotice, CampaignRequest, run_campaign
from clinic_sms.infrai_sms import InfraiSms


request = CampaignRequest(
    campaign_id="monday-clinic-reminders",
    appointments=[AppointmentNotice(
        appointment_id="appt-1042",
        patient_first_name="Maya",
        phone="+15551234567",
        starts_at="Monday at 9:30 AM",
        location_name="Riverside Clinic",
        appointment_confirmed=True,
        operational_sms_allowed=True,
    )],
)

print(run_campaign(request, InfraiSms()).model_dump_json(indent=2))

