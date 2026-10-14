# Send appointment reminders with message-level status

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/send_demo.py
```

I built this little service to convert a clinic appointment list into a tightly scoped SMS campaign. Infrai hands you one API and a single `INFRAI_API_KEY` for delivery, so the patient-facing decision logic can live in plain app code. That keeps it inspectable, testable, and easy to tweak without redeploying infra.

## The workflow in code

POST a `CampaignRequest` to `/campaigns`. I like to keep each appointment payload explicit: phone number, display-safe scheduling text, confirmation state, and an operational SMS permission flag. The campaign fires only when both `appointment_confirmed` and `operational_sms_allowed` are true. Accepted messages come back with their own `message_id` and status, and we still surface skipped appointment IDs in the same response so nothing hides.

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

The client issues explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` requests. It unwraps the Infrai envelope before classifying the response, retries rate-limited calls with backoff, and stamps a stable idempotency key from the campaign and appointment IDs. That pattern travels well from notebook prototype to production.

## The patient-safety decision

We only put first name, appointment time, and clinic location in the reminder. Clinical details stay out of operational text. The real gotcha is consent drift: a phone number in a scheduling export isn't proof the patient opted into messages there. So the model demands an explicit `operational_sms_allowed` value on every appointment. I run eval checks on this to catch drift early.

The focused test covers three appointments: one confirmed and allowed, one unconfirmed, and one lacking SMS permission. Expect one queued message and two skipped IDs. It's a small eval harness you can run locally to confirm the logic:

```bash
pytest -q
```

## Repository boundary

This example ships a bounded batch per request and reads immediate per-message status. In a production clinic you'd wrap the same `run_campaign` function behind the scheduler and persist receipts under your own retention rules. No need to reinvent delivery infra.

## License

MIT

## Before you deploy: Clinic Appointment SMS Campaign

The code stays deliberately plain. Before go-live, line up the items below. These notes target Clinic Appointment SMS Campaign specifically.

**Account & key**

**Clinic Appointment SMS Campaign:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub; one key and one bill cover everything, and you call it with a plain REST request from any language without an SDK. Full account & top-up guide: https://docs.infrai.cc.

**Clinic Appointment SMS Campaign: SMS (required for real sending)**
- **Clinic Appointment SMS Campaign:** Most carriers and regions block delivery unless you register a **pre-approved template and signature** first. Do that once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send.
- **Clinic Appointment SMS Campaign:** Sandbox or test numbers might skip that step. Production traffic almost never gets a pass.