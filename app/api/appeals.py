import re
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.dependencies import save_appeals
from enum import Enum
from datetime import datetime


class ProblemTypeEnum(str, Enum):
    no_connection = "no_connection"
    phone_issue = "phone_issue"
    no_messages = "mo_messages"

class Appeal(BaseModel):
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date = Field(...)
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=10, max_length=12)
    problem_types: list[ProblemTypeEnum] = Field(..., min_items=1)
    problem_at: datetime = Field(...)

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str) -> str:
        if not re.fullmatch(r"\+?[0-9]+", v):
            raise ValueError("Phone must contain only digits and an optional leading plus")
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10 or len(digits) > 11:
            raise ValueError("Phone must have 10 or 11 digits")
        if len(digits) == 10 and digits.startswith("9"):
            return "+7" + digits
        if len(digits) == 11 and digits.startswith("7"):
            return "+7" + digits[1:]
        if len(digits) == 11 and digits.startswith("8"):
            return "+7" + digits[1:]
        raise ValueError("Phone number must be in format +7dddddddddd (10 digits after +7)")

router = APIRouter()

@router.post("/appeals")
async def create_appeal(appeal: Appeal):
    try:
        appeal = Appeal(**appeal.model_dump())
        save_appeals(appeal.model_dump(mode="json"))
        return {"message": "Appeal created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
