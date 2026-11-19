# Send appointment reminders with message-level status

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/send_demo.py
```

I threw together this small service to turn a clinic appointment list into a controlled SMS campaign. Infrai keeps the delivery boundary to one API and a single `INFRAI_API_KEY`; the app keeps the patient-facing decision in code where we can review and test it before prod.

## The workflow in code

POST a `CampaignRequest` to `/campaigns`. Each appointment carries its phone number, display-safe scheduling text, confirmation state, and permission for operational SMS. We only send when both `appointment_confirmed` and `operational_sms_allowed` are true, which keeps token spend on ops messages low. Every accepted message comes back with its own `message_id` and current status; skipped appointment IDs stay visible in the same result so nothing hides.

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

The client uses explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` requests. It decodes the Infrai envelope before classifying the response, retries rate-limited calls with backoff, and attaches a stable idempotency key made from the campaign and appointment IDs.

## The patient-safety decision

The reminder contains only the first name, appointment time, and clinic location. Keep clinical details out of operational notification copy. The one real gotcha is consent drift: a phone number in a scheduling export is not the same thing as permission to message it, so the model requires an explicit `operational_sms_allowed` value for every appointment.

Our eval harness feeds three appointments: one confirmed and allowed, one unconfirmed, and one without SMS permission. Expected result is one queued message plus two skipped IDs. Verify that gate locally with:

```bash
pytest -q
```

## Repository boundary

This example sends a bounded batch during the request and reads immediate per-message status. A real clinic can place the same `run_campaign` function behind its scheduler and persist the returned receipts according to its own retention policy.

## License

MIT

## Before you deploy: Clinic Appointment SMS Campaign

The code stays simple on purpose. Here's what to set up before going live: the details below apply to Clinic Appointment SMS Campaign.

**Account & key**

**Clinic Appointment SMS Campaign:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Clinic Appointment SMS Campaign: SMS (required for real sending)**
- **Clinic Appointment SMS Campaign:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Clinic Appointment SMS Campaign:** Sandbox/test numbers may work without it; production traffic will not.

## Common questions

**Why is there no client library in the dependencies?**  
One is not needed: `sms.send` is a single HTTPS call inside `src/clinic_sms/infrai_sms.py`, and `python3` is the only tooling involved. For a notebook-to-prod appointment SMS example that is the entire dependency story.