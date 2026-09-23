from fastapi import FastAPI
from schemas.ticket import TicketPayload
from app.services.groq import gen_groq_json
from services.quality import quality_check

app = FastAPI()


@app.post("/v1/merchant/tickets/triage")
async def triage_ticket(ticket_payload: TicketPayload):
    ticket_payload = ticket_payload.dict()
    # Perform quality check on the payload
    quality_result = quality_check(ticket_payload)

    if quality_result["data_quality"]["score"] < 50:
        return {"message": "Ticket failed quality check"}

    ai_dispatch = await gen_groq_json(quality_result)
    quality_result["ai_dispatch"] = ai_dispatch 
    return {quality_result}