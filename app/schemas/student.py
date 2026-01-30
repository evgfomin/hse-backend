from pydantic import BaseModel, Field, ConfigDict


class StudentBase(BaseModel):
    id: int
    last_name: str
    first_name: str
    faculty: str
    course: str
    score: int

class StudentCreate(BaseModel):
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    faculty: str = Field(..., min_length=1, max_length=100)
    course: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=1, le=100)

class Student(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)