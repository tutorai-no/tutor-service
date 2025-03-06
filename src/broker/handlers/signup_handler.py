from uuid import UUID
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr


class SubscriptionSchema(BaseModel):
    """Pydantic model for Subscription."""

    id: Optional[int]
    name: str
    description: Optional[str] = None
    price: Decimal
    active: bool

    class Config:
        orm_mode = True


class UserSchema(BaseModel):
    """Pydantic model for User."""

    id: UUID
    username: str
    email: EmailStr
    subscription: Optional[SubscriptionSchema] = None
    phone_number: Optional[str] = None
    heard_about_us: Optional[str] = None
    other_heard_about_us: Optional[str] = None

    class Config:
        orm_mode = True
