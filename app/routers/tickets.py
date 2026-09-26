from fastapi import APIRouter, HTTPException, status

from app.schemas.ticket import TicketRequestModel
from app.services.groq import gen_groq_json
from app.services.quality import calculate_quality_score

router = APIRouter()  # Create the router instance


@router.post(
    "/v1/merchant/tickets/triage",
    summary="Triage an incoming merchant support ticket",
    description=(
        "Validates, scores, and routes an inbound ticket through three sequential gates: "
        "structural validation (Pydantic), data quality profiling (0-100 score), and "
        "AI-powered categorization. Tickets that fail validation or score below 50 are "
        "rejected before any AI cost is incurred."
    ),
    responses={
        422: {"description": "Structural validation failed - missing or malformed fields"},
        400: {"description": "Ticket passed structural validation but failed the quality gate (score < 50)"},
        200: {"description": "Ticket passed both gates and was successfully classified"},
    },
)
async def triage_ticket(ticket: TicketRequestModel):
    # 1. Safely extract merchant_tier string whether it's an Enum or str
    merchant_tier = ticket.merchant_tier
    merchant_tier_str = (
        merchant_tier.value if hasattr(merchant_tier, "value") else merchant_tier
    )

    # 2. Run your Quality Gate
    quality_result = calculate_quality_score(
        issue_description=ticket.issue_description,
        merchant_tier=merchant_tier_str,
    )

    # 3. Gate 2 Rejection: Raise HTTP 400 if score < 50
    if quality_result["score"] < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "TICKET_QUALITY_GATE_FAILED",
                "message": (
                    "The ticket description failed minimum quality threshold standards "
                    "and could not be automatically processed."
                ),
                "score": quality_result["score"],
                "status": quality_result["status"],
                "flags": quality_result["flags"],
                "guidance": (
                    "Please revise the issue description to include specific technical "
                    "identifiers (e.g., transaction ID, HTTP status code, or endpoint path), "
                    "remove HTML/excessive formatting, and provide adequate detail."
                ),
            },
        )

    # 4. Combine model data + sanitized text into payload for Groq
    # payload_for_ai = {
    #     **ticket.model_dump(),  
    #     "cleaned_description": quality_result["cleaned_text"],
    #     "quality_score": quality_result["score"],
    #     "quality_flags": quality_result["flags"],
    # }
    payload_for_ai = {
    "ticket_id": ticket.ticket_id,
    "merchant_id": ticket.merchant_id,
    "merchant_tier": merchant_tier_str,
    "contact_email": ticket.contact_email,
    "processing_timestamp": ticket.timestamp.isoformat(),
    "issue_description": quality_result["cleaned_text"],
    "data_quality": {
        "score": quality_result["score"],
        "status": quality_result["status"],
        "flags": quality_result["flags"],
    },
}

    # 5. Hand off to Mentee B's Groq dispatch function
    ai_dispatch = await gen_groq_json(payload_for_ai)

    if ai_dispatch is None:
        ai_dispatch = {
            "category": "Unclassified",
            "sla_urgency": "P3 (Standard)",
            "auto_route_to": "Merchant Support Tier 1",
            "reasoning": "AI classification service was unavailable; routed to standard support queue for manual triage.",
        }

    # 6. Return structured response
    return {
        "status": "SUCCESS",
        "quality_report": quality_result,
        "ai_dispatch": ai_dispatch,
    }