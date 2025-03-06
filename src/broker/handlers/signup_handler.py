from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    subscription: Optional[str] = None
    phone_number: Optional[str] = None
    heard_about_us: Optional[str] = None
    other_heard_about_us: Optional[str] = None

    class Config:
        orm_mode = True
