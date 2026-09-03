from dataclasses import dataclass
from typing import Any, Protocol, get_type_hints

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Keep the focused campaign logic usable without extras installed.
    class BaseModel:
        def __init__(self, **values: Any):
            fields = get_type_hints(type(self))
            missing = [name for name in fields if name not in values]
            if missing:
                raise TypeError(f"missing required fields: {', '.join(missing)}")
            for name, value in values.items():
                setattr(self, name, value)

        def model_dump(self) -> dict[str, Any]:
            return {name: getattr(self, name) for name in get_type_hints(type(self))}

    def Field(**_: Any) -> Any:
        return None


class AppointmentNotice(BaseModel):
    appointment_id: str = Field(min_length=1)
    patient_first_name: str = Field(min_length=1)
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    starts_at: str = Field(min_length=1)
    location_name: str = Field(min_length=1)
    appointment_confirmed: bool
    operational_sms_allowed: bool


class CampaignRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    appointments: list[AppointmentNotice] = Field(min_length=1, max_length=100)


class MessageReceipt(BaseModel):
    appointment_id: str
    message_id: str
    status: str


class CampaignResult(BaseModel):
    campaign_id: str
    sent: list[MessageReceipt]
    skipped_appointment_ids: list[str]


class SmsGateway(Protocol):
    def send(self, to: str, message: str, idempotency_key: str) -> dict: ...
    def status(self, message_id: str) -> dict: ...


def render_reminder(item: AppointmentNotice) -> str:
    return (
        f"Hi {item.patient_first_name}, your appointment is {item.starts_at} "
        f"at {item.location_name}. Reply to the clinic if your plans changed."
    )


def run_campaign(request: CampaignRequest, gateway: SmsGateway) -> CampaignResult:
    sent: list[MessageReceipt] = []
    skipped: list[str] = []
    for item in request.appointments:
        if not (item.appointment_confirmed and item.operational_sms_allowed):
            skipped.append(item.appointment_id)
            continue
        delivery = gateway.send(
            item.phone,
            render_reminder(item),
            f"{request.campaign_id}:{item.appointment_id}",
        )
        message_id = delivery["message_id"]
        current = gateway.status(message_id)
        sent.append(MessageReceipt(
            appointment_id=item.appointment_id,
            message_id=message_id,
            status=current["status"],
        ))
    return CampaignResult(
        campaign_id=request.campaign_id,
        sent=sent,
        skipped_appointment_ids=skipped,
    )
