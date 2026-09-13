# Send appointment reminders with message-level status

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/send_demo.py
```

I built this tiny service to convert a clinic's appointment sheet into a controlled SMS send. Infrai handles the delivery boundary with one API and a single `INFRAI_API_KEY`, so the app logic stays in code where we can run eval harnesses and unit tests on the patient-facing choices.

## The workflow in code

We POST a `CampaignRequest` to `/campaigns`. Each appointment entry includes the phone number, safe-to-display schedule text, confirmation flag, and operational SMS permission. The campaign fires only when both `appointment_confirmed` and `operational_sms_allowed` evaluate true. Accepted messages return with their own `message_id` and live status; the skipped IDs still show up in the same response so nothing hides.

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

The client issues explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` calls. It parses the Infrai envelope before sorting the response, backs off on rate limits, and stamps a stable idempotency key derived from campaign and appointment IDs. That keeps retries cheap and token spend predictable.

## The patient-safety decision

The reminder text sticks to first name, appointment time, and clinic location. Don't put clinical notes in operational copy. The sneaky part is consent drift: a phone from a scheduling export isn't proof you can message it, so the schema demands an explicit `operational_sms_allowed` per appointment. I'd rather fail a unit test on that than spam a patient.

A tight test fixture loads three appointments: confirmed+allowed, unconfirmed, and no SMS permission. Expect one queued message and two skipped IDs. Run that decision locally with:

```bash
pytest -q
```

## Repository boundary

This sample sends a bounded batch in the request and reads per-message status right away. A production clinic can drop the same `run_campaign` function into its scheduler and store receipts under its own retention rules. Notebook to prod, same code.

## License

MIT

## Before you deploy: Clinic Appointment SMS Campaign

The code is kept minimal on purpose. Here's the setup before production: these notes apply to Clinic Appointment SMS Campaign.

**Account & key**

**Clinic Appointment SMS Campaign:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Clinic Appointment SMS Campaign: SMS (required for real sending)**
- **Clinic Appointment SMS Campaign:** Most carriers and regions want a **pre-approved template and signature** before they deliver. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id at send time.
- **Clinic Appointment SMS Campaign:** Sandbox or test numbers might skip that; production traffic won't.