from clinic_sms.appointment_campaign import AppointmentNotice, CampaignRequest, run_campaign


class RecordingGateway:
    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, message: str, idempotency_key: str) -> dict:
        self.sent.append((to, message, idempotency_key))
        return {"message_id": "msg-42"}

    def status(self, message_id: str) -> dict:
        assert message_id == "msg-42"
        return {"status": "queued"}


def appointment(identifier: str, confirmed: bool, allowed: bool) -> AppointmentNotice:
    return AppointmentNotice(
        appointment_id=identifier,
        patient_first_name="Maya",
        phone="+15551234567",
        starts_at="Monday at 9:30 AM",
        location_name="Riverside Clinic",
        appointment_confirmed=confirmed,
        operational_sms_allowed=allowed,
    )


def test_campaign_sends_only_confirmed_and_allowed_appointments():
    gateway = RecordingGateway()
    request = CampaignRequest(campaign_id="clinic-2026-08-31", appointments=[
        appointment("send-me", True, True),
        appointment("not-confirmed", False, True),
        appointment("not-allowed", True, False),
    ])

    result = run_campaign(request, gateway)

    assert len(gateway.sent) == 1
    assert gateway.sent[0][2] == "clinic-2026-08-31:send-me"
    assert result.sent[0].model_dump() == {
        "appointment_id": "send-me", "message_id": "msg-42", "status": "queued"
    }
    assert result.skipped_appointment_ids == ["not-confirmed", "not-allowed"]

