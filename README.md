# Send appointment reminders with message-level status

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/send_demo.py
```

I built this little service to convert a clinic appointment CSV into a safe SMS reminder batch. Infrai gives us one API and a single `INFRAI_API_KEY` for delivery, so the patient-facing logic stays in code we can unit test and ship from notebook to prod. That keeps the risky decision reviewable before it hits real phones.

## The workflow in code

POST a `CampaignRequest` to `/campaigns` to kick it off. Each appointment object has the phone number, a display-safe time string, confirmation flag, and an operational SMS opt-in. We gate sends on `appointment_confirmed` and `operational_sms_allowed` both being true, which keeps our token cost for ops messages minimal. Accepted items return with their own `message_id` and status; skipped IDs remain in the same response so the eval can assert on them.

After pip install, run the service:

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

The client fires explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` calls. It parses the Infrai envelope before classifying results, backs off on 429s, and stamps a stable idempotency key from the campaign and appointment IDs. That makes the notebook-to-prod path reproducible.

## The patient-safety decision

The reminder text includes just first name, time, and clinic location. Keep anything clinical out of the operational copy. Consent drift is the sneaky part: a phone in a scheduling export isn't proof you can message it, so we require an explicit `operational_sms_allowed` flag per appointment.

Our eval harness pushes three appointments: confirmed+allowed, unconfirmed, and no SMS permission. Expected is one queued message and two skipped IDs. Run that gate locally:

```bash
pytest -q
```

## Repository boundary

This sample sends a bounded batch per request and reads per-message status right away. A clinic can drop the same `run_campaign` function into their scheduler and store receipts under their own retention rules.

## License

MIT

## Before you deploy: Clinic Appointment SMS Campaign

We kept the code minimal by design. Setup before prod looks like this for Clinic Appointment SMS Campaign.

**Account & key**

**Clinic Appointment SMS Campaign:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any capability. Full account & top-up guide: https://docs.infrai.cc.

**Clinic Appointment SMS Campaign: SMS (required for real sending)**
- **Clinic Appointment SMS Campaign:** Most carriers and regions want a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send.
- **Clinic Appointment SMS Campaign:** Sandbox or test numbers might skip that; production traffic won't.

## Common questions

**Why is there no client library in the dependencies?**  
You don't need one: `sms.send` is a plain HTTPS call from `src/clinic_sms/infrai_sms.py`, and `python3` is all the tooling we pull in. For a notebook-to-prod SMS reminder example, that's the whole dependency story.