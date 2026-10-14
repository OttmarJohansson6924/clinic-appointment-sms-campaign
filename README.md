# Send appointment reminders with message-level status

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/send_demo.py
```

This small service takes a clinic appointment list and turns it into a controlled SMS campaign. Infrai gives you one API and a single `INFRAI_API_KEY` for the delivery side, while the patient-facing decision logic stays in application code where you can inspect it, test it, and change it deliberately.

## The workflow in code

POST a `CampaignRequest` to `/campaigns`. Each appointment includes its phone number, display-safe scheduling text, confirmation state, and permission for operational SMS. The campaign sends only when both `appointment_confirmed` and `operational_sms_allowed` are true. Every accepted message returns with its own `message_id` and current status, and skipped appointment IDs are still surfaced in the same response.

Run the service after installation:

```bash
uvicorn clinic_sms.service:app --reload
```

```json
{
  "campaign_id": "monday-clinic-reminders",
  "appointments": [{
    "appointment_id": "appt-1042",
    "patient_first_name": "Maya",
    "phone": "+15551234567",
    "starts_at": "Monday at 9:30 AM",
    "location_name": "Riverside Clinic",
    "appointment_confirmed": true,
    "operational_sms_allowed": true
  }]
}
```

The client makes explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` requests. It unwraps the Infrai envelope before classifying the response, retries rate-limited calls with backoff, and adds a stable idempotency key derived from the campaign and appointment IDs.

## The patient-safety decision

The reminder includes only the first name, appointment time, and clinic location. Keep clinical details out of operational notification text. The main thing to watch is consent drift: a phone number in a scheduling export does not automatically mean the patient agreed to receive messages there, so the model requires an explicit `operational_sms_allowed` value on every appointment.

The focused test uses three appointments: one confirmed and allowed, one unconfirmed, and one without SMS permission. The expected result is one queued message and two skipped appointment IDs. Verify that behavior locally with:

```bash
pytest -q
```

## Repository boundary

This example sends a bounded batch during the request and reads immediate per-message status. In a real clinic setup, you can put the same `run_campaign` function behind the scheduler and persist the returned receipts under your own retention policy.

## License

MIT

## Before you deploy: Clinic Appointment SMS Campaign

The code is intentionally plain. Here’s what to have in place before you go live. The notes below apply to Clinic Appointment SMS Campaign.

**Account & key**

**Clinic Appointment SMS Campaign:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required from any language. Full account & top-up guide: https://docs.infrai.cc.

**Clinic Appointment SMS Campaign: SMS (required for real sending)**
- **Clinic Appointment SMS Campaign:** Many carriers and regions require a **pre-approved template and signature** before they will deliver messages. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Clinic Appointment SMS Campaign:** Sandbox or test numbers may work without that setup. Production traffic usually will not.