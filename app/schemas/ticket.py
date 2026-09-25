from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ValidationError


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