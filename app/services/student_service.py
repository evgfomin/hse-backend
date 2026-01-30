from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositoreis.student_repository import StudentRepository
from app.schemas.student import StudentCreate


class StudentService:
    def __init__(self, db: AsyncSession):
        self.repo = StudentRepository(db)

    async def get_student_by_id(self, student_id: int):
        return await self.repo.get(student_id)

    async def create_student(self, student: StudentCreate):
        return await self.repo.create(student)

    async def update_student(self, student_id: int, student: StudentCreate):
        return await self.repo.update(student_id, student)

    async def get_all_students(self):
        return await self.repo.get_all()

    async def sync_csv(self, csv_file: Path):
        res = await self.repo.get_all()
        if len(res) == 0:
            return await self.repo.sync_csv(csv_file)
        else:
            return None

    async def delete_students(self, student_ids: List[int]):
        try:
            await self.repo.delete(student_ids)
            return True
        except Exception as e:
            print(e)
            return False
