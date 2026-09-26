from fastapi import APIRouter, HTTPException, status
from app.schemas.ticket import TicketRequestModel as TicketPayload, TriageResponse
from app.services.groq import gen_groq_json
from app.services.quality import calculate_quality_score

router = APIRouter()



@router.post("/v1/merchant/tickets/triage")
async def triage_ticket(ticket_payload: TicketPayload) -> TriageResponse:
    ticket_dict = ticket_payload.model_dump()

    # Perform quality check on the payload
    quality_result = calculate_quality_score(
        issue_description=ticket_dict["issue_description"],
        merchant_tier=ticket_dict["merchant_tier"]
    )

    if quality_result["score"] < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "TICKET_QUALITY_CHECK_FAILED",
                "message": "Ticket description failed minimum quality and hygiene requirements.",
                "score": quality_result["score"],
                "passing_threshold": 50,
                "triggered_flags": quality_result.get("flags", []),
            }
        )
    
    llm_input = { 
                    "merchant_tier": ticket_dict["merchant_tier"], 
                    "issue_description": quality_result["cleaned_text"]
             }


    ai_dispatch = await gen_groq_json(llm_input)

    response = ticket_dict.copy()
    response["data_quality"] = quality_result
    response["ai_dispatch"] = ai_dispatch 
    return response