import csv
from pathlib import Path

from sqlalchemy import select, update, Boolean, delete, func
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.student import Student as StudentModel
from app.schemas.student import StudentCreate


class StudentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_csv(self, csv_file: Path) -> List[StudentModel]:
        students = []
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student = StudentModel(
                    last_name=row['Фамилия'],
                    first_name=row['Имя'],
                    faculty=row['Факультет'],
                    course=row['Курс'],
                    score=int(row['Оценка'])
                )
                self.session.add(student)
                students.append(student)
        await self.session.commit()
        return students

    async def get(self, item_id: int) -> Optional[StudentModel]:
        result = await self.session.execute(
            select(StudentModel).where(StudentModel.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[StudentModel]:
        result = await self.session.execute(select(StudentModel))
        return list(result.scalars().all())

    async def create(self, student: StudentCreate) -> StudentModel:
        db_item = StudentModel(**student.model_dump())
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return db_item

    async def update(self, student_id: int, student: StudentCreate) -> Optional[StudentModel]:
        await self.session.execute(
            update(StudentModel).where(StudentModel.id == student_id).values(student.model_dump())
        )
        await self.session.commit()
        return await self.get(student_id)

    async def delete(self, student_ids: List[int]) -> bool:
        print(student_ids)
        await self.session.execute(
            delete(StudentModel).where(StudentModel.id.in_(student_ids))
        )
        await self.session.commit()
        return True

    async def unique_courses(self):
        result = await self.session.execute(
            select(StudentModel.course).distinct()
        )
        return result.scalars().all()

    async def average_score_by_faculty(self, faculty: str) -> float:
        result = await self.session.execute(
            select(func.avg(StudentModel.score)).where(StudentModel.faculty == faculty)
        )
        return result.scalar() or 0.0

    async def students_with_score(self) -> List[StudentModel]:
        result = await self.session.execute(
            select(StudentModel).where(StudentModel.score <= 30)
        )
        return list(result.scalars().all())