from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class MerchantTier(str, Enum):
    # TODO: Specify the only allowed (3) tiers
    STARTER = 'Starter'
    GROWTH = 'Growth'
    ENTERPRISE = 'Enterprise'


class TicketRequestModel(BaseModel):
    ticket_id: str = Field(pattern=r"^TCK-\d{4,8}$")
    # Must start with mer_ followed by alphanumericcharacters (e.g., mer_live_99812).
    merchant_id: str = Field(pattern=r"^mer_[a-zA-Z0-9_]+$")
    merchant_tier: MerchantTier
    contact_email: EmailStr
    timestamp: datetime
    issue_description: str = Field(min_length=15, max_length=2000)

class QualityStatus(str, Enum):
    EXCELLENT = 'EXCELLENT'
    ACCEPTABLE = 'ACCEPTABLE'
    REJECTED = 'REJECTED'

class SLA_Urgency(str, Enum):
    CRITICAL = 'P1 (Critical Outage)'
    HIGH = 'P2 (High)'
    STANDARD = 'P3 (Standard)'

class Category(str, Enum):
    TRANSACTION_FAILURE = 'Transaction Failure'
    API_WEBHOOKS = 'API / Webhooks'
    SETTLEMENT_PAYOUTS = 'Settlement & Payouts'
    ACCOUNT_ACCESS = 'Account Access'
    GENERAL_INQUIRY = 'General Inquiry'


class QualityReport(BaseModel):
     # TODO: score (int), status (str), flags (a list of strings)
    score: int
    status: QualityStatus
    flags: list[str]
    cleaned_text: str

class AIDispatch(BaseModel):
    category: Category
    sla_urgency: SLA_Urgency
    auto_route_to: str
    reasoning: str

class LLMInput(BaseModel):
    merchant_tier: MerchantTier
    issue_description: str

class TriageResponse(BaseModel):
    ticket_id: str
    merchant_id: str
    merchant_tier: MerchantTier
    timestamp: datetime
    data_quality: QualityReport
    ai_dispatch: AIDispatch
