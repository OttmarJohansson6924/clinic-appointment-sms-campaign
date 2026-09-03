from fastapi import FastAPI, HTTPException

from .appointment_campaign import CampaignRequest, CampaignResult, run_campaign
from .infrai_sms import InfraiError, InfraiSms

app = FastAPI(title="Clinic appointment SMS")


@app.post("/campaigns", response_model=CampaignResult)
def send_campaign(request: CampaignRequest) -> CampaignResult:
    try:
        return run_campaign(request, InfraiSms())
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=exc.detail) from exc

