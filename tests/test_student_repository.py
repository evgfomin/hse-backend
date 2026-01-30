import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.student import Student
from app.database import Base
from app.repositoreis.student_repository import StudentRepository
from app.schemas.student import StudentCreate


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session):
    return StudentRepository(session)


@pytest.mark.asyncio
async def test_create_student(repo):
    student_data = StudentCreate(
        last_name="Иванов",
        first_name="Иван",
        faculty="ФПМИ",
        course="Информатика",
        score=85
    )

    created = await repo.create(student_data)

    assert created.id is not None
    assert created.last_name == "Иванов"
    assert created.first_name == "Иван"
    assert created.faculty == "ФПМИ"
    assert created.score == 85


@pytest.mark.asyncio
async def test_get_student(repo):
    student_data = StudentCreate(
        last_name="Петров",
        first_name="Петр",
        faculty="ФТФ",
        course="Физика",
        score=90
    )

    created = await repo.create(student_data)
    fetched = await repo.get(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.last_name == "Петров"


@pytest.mark.asyncio
async def test_get_student_not_found(repo):
    fetched = await repo.get(9999)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_all_students(repo):
    for i in range(3):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="АВТФ",
            course="Механика",
            score=70 + i
        ))

    students = await repo.get_all()

    assert len(students) == 3


@pytest.mark.asyncio
async def test_update_student(repo):
    student_data = StudentCreate(
        last_name="Сидоров",
        first_name="Сидор",
        faculty="РЭФ",
        course="Электроника",
        score=75
    )

    created = await repo.create(student_data)

    updated_data = StudentCreate(
        last_name="Сидоров",
        first_name="Сидор",
        faculty="РЭФ",
        course="Электроника",
        score=95
    )

    updated = await repo.update(created.id, updated_data)

    assert updated.score == 95


@pytest.mark.asyncio
async def test_delete_students(repo):
    ids = []
    for i in range(3):
        student = await repo.create(StudentCreate(
            last_name=f"Удаляемый{i}",
            first_name="Тест",
            faculty="ФЛА",
            course="Лингвистика",
            score=60
        ))
        ids.append(student.id)

    result = await repo.delete(ids)

    assert result is True

    for student_id in ids:
        fetched = await repo.get(student_id)
        assert fetched is None


@pytest.mark.asyncio
async def test_unique_courses(repo):
    courses = ["Математика", "Физика", "Математика", "Химия", "Физика"]

    for i, course in enumerate(courses):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФПМИ",
            course=course,
            score=80
        ))

    unique = await repo.unique_courses()

    assert len(unique) == 3
    assert set(unique) == {"Математика", "Физика", "Химия"}


@pytest.mark.asyncio
async def test_average_score_by_faculty(repo):
    scores = [80, 90, 100]

    for i, score in enumerate(scores):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФТФ",
            course="Физика",
            score=score
        ))

    avg = await repo.average_score_by_faculty("ФТФ")

    assert avg == 90.0


@pytest.mark.asyncio
async def test_average_score_by_faculty_not_found(repo):
    avg = await repo.average_score_by_faculty("НЕСУЩЕСТВУЮЩИЙ")

    assert avg == 0.0
