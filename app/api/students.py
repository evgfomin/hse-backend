from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.student import Student, StudentCreate
from app.services.student_service import StudentService

router = APIRouter()


@router.post("/students", tags=['Students'], response_model=Student)
async def create_student(student: StudentCreate, db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.create_student(student)
    return Student.model_validate(response)


@router.get("/students", tags=['Students'], response_model=List[Student])
async def get_all_students(db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.get_all_students()
    if response is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return [Student.model_validate(s) for s in response]


@router.get("/students/csv", tags=['Students'], response_model=List[Student])
async def sync_csv(db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.sync_csv(Path("./app/students.csv"))
    if response is None:
        raise HTTPException(status_code=404, detail="CSV hasn't been synced")
    return [Student.model_validate(s) for s in response]


@router.get("/students/{student_id}", tags=['Students'], response_model=Student)
async def get_student_by_id(student_id: int, db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.get_student_by_id(student_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return Student.model_validate(response)


@router.put("/students/{student_id}", tags=['Students'], response_model=Student)
async def update_student(student_id: int, student: StudentCreate, db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.update_student(student_id, student)
    if response is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return Student.model_validate(response)


@router.delete("/students", tags=['Students'])
async def delete_students(student_ids: List[int], db: AsyncSession = Depends(get_db)):
    service = StudentService(db)
    response = await service.delete_students(student_ids)
    if response is not True:
        raise HTTPException(status_code=404, detail="Students were not deleted")
    return {"deleted": True}
