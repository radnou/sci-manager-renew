from typing import Literal

from pydantic import BaseModel, Field


class CheckoutSessionCreateRequest(BaseModel):
    price_id: str = Field(min_length=3)
    mode: Literal["subscription", "payment"] = "subscription"


class CheckoutSessionCreateResponse(BaseModel):
    url: str


class StripeWebhookResponse(BaseModel):
    status: Literal["success"]

