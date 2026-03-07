from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssocieBase(BaseModel):
    id_sci: str
    nom: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    part: float = Field(gt=0, le=100)
    role: str = Field(default="associe", min_length=2, max_length=40)
    user_id: str | None = None


class AssocieCreate(AssocieBase):
    pass


class AssocieUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    part: float | None = Field(default=None, gt=0, le=100)
    role: str | None = Field(default=None, min_length=2, max_length=40)


class AssocieResponse(AssocieBase):
    id: str
    is_account_member: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
