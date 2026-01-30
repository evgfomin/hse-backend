"""
ДЗ 4 — Работа с базами данных: FastAPI, SQLAlchemy, Alembic
Tests for SQLAlchemy models and database operations.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.student import Student
from app.database import Base
from app.repositoreis.student_repository import StudentRepository
from app.schemas.student import StudentCreate, StudentBase


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create test database session."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def repo(session):
    """Create StudentRepository instance."""
    return StudentRepository(session)


# ===== SQLAlchemy Model Tests =====

@pytest.mark.asyncio
async def test_student_model_creation(session):
    """Test Student SQLAlchemy model creation."""
    student = Student(
        last_name="Иванов",
        first_name="Иван",
        faculty="ФПМИ",
        course="Информатика",
        score=85
    )
    session.add(student)
    await session.commit()
    await session.refresh(student)

    assert student.id is not None
    assert student.last_name == "Иванов"
    assert student.first_name == "Иван"
    assert student.faculty == "ФПМИ"
    assert student.course == "Информатика"
    assert student.score == 85


@pytest.mark.asyncio
async def test_student_model_table_name(session):
    """Test Student model table name."""
    assert Student.__tablename__ == "students"


# ===== Repository INSERT Tests =====

@pytest.mark.asyncio
async def test_repository_insert_student(repo):
    """Test inserting a student via repository."""
    student_data = StudentCreate(
        last_name="Петров",
        first_name="Петр",
        faculty="ФТФ",
        course="Физика",
        score=92
    )
    created = await repo.create(student_data)

    assert created.id is not None
    assert created.last_name == "Петров"
    assert created.score == 92


@pytest.mark.asyncio
async def test_repository_insert_multiple_students(repo):
    """Test inserting multiple students."""
    students_data = [
        StudentCreate(last_name="Иванов", first_name="Иван", faculty="ФПМИ", course="Математика", score=80),
        StudentCreate(last_name="Петров", first_name="Петр", faculty="ФТФ", course="Физика", score=85),
        StudentCreate(last_name="Сидоров", first_name="Сидор", faculty="РЭФ", course="Электроника", score=90),
    ]

    created_students = []
    for data in students_data:
        created = await repo.create(data)
        created_students.append(created)

    assert len(created_students) == 3
    assert all(s.id is not None for s in created_students)


@pytest.mark.asyncio
async def test_repository_insert_cyrillic_names(repo):
    """Test inserting student with Cyrillic names."""
    student_data = StudentCreate(
        last_name="Козлов",
        first_name="Владимир",
        faculty="АВТФ",
        course="Теоретическая механика",
        score=78
    )
    created = await repo.create(student_data)

    assert created.last_name == "Козлов"
    assert created.first_name == "Владимир"
    assert created.course == "Теоретическая механика"


# ===== Repository SELECT Tests =====

@pytest.mark.asyncio
async def test_repository_select_by_id(repo):
    """Test selecting student by ID."""
    student_data = StudentCreate(
        last_name="Тестов",
        first_name="Тест",
        faculty="ФПМИ",
        course="Тест",
        score=100
    )
    created = await repo.create(student_data)
    fetched = await repo.get(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.last_name == "Тестов"


@pytest.mark.asyncio
async def test_repository_select_nonexistent(repo):
    """Test selecting non-existent student."""
    fetched = await repo.get(99999)
    assert fetched is None


@pytest.mark.asyncio
async def test_repository_select_all(repo):
    """Test selecting all students."""
    for i in range(5):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФПМИ",
            course="Курс",
            score=70 + i
        ))

    students = await repo.get_all()
    assert len(students) == 5


@pytest.mark.asyncio
async def test_repository_select_all_empty(repo):
    """Test selecting all when database is empty."""
    students = await repo.get_all()
    assert students == []


# ===== Students by Faculty Tests =====

@pytest.mark.asyncio
async def test_repository_students_by_faculty(repo):
    """Test getting students by faculty."""
    # Create students in different faculties
    await repo.create(StudentCreate(
        last_name="Иванов", first_name="Иван", faculty="ФПМИ", course="Курс", score=80
    ))
    await repo.create(StudentCreate(
        last_name="Петров", first_name="Петр", faculty="ФТФ", course="Курс", score=85
    ))
    await repo.create(StudentCreate(
        last_name="Сидоров", first_name="Сидор", faculty="ФПМИ", course="Курс", score=90
    ))

    # Note: get_all doesn't filter by faculty, so this tests all students
    all_students = await repo.get_all()
    fpmi_students = [s for s in all_students if s.faculty == "ФПМИ"]
    assert len(fpmi_students) == 2


# ===== Unique Courses Tests =====

@pytest.mark.asyncio
async def test_repository_unique_courses(repo):
    """Test getting unique courses."""
    courses = ["Математика", "Физика", "Математика", "Химия", "Физика", "История"]

    for i, course in enumerate(courses):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФПМИ",
            course=course,
            score=80
        ))

    unique = await repo.unique_courses()

    assert len(unique) == 4
    assert set(unique) == {"Математика", "Физика", "Химия", "История"}


@pytest.mark.asyncio
async def test_repository_unique_courses_empty(repo):
    """Test getting unique courses from empty database."""
    unique = await repo.unique_courses()
    assert unique == []


@pytest.mark.asyncio
async def test_repository_unique_courses_single(repo):
    """Test getting unique courses with single course."""
    await repo.create(StudentCreate(
        last_name="Студент",
        first_name="Тест",
        faculty="ФПМИ",
        course="Единственный курс",
        score=80
    ))

    unique = await repo.unique_courses()
    assert unique == ["Единственный курс"]


# ===== Average Score by Faculty Tests =====

@pytest.mark.asyncio
async def test_repository_average_score_by_faculty(repo):
    """Test calculating average score by faculty."""
    scores = [70, 80, 90, 100]

    for i, score in enumerate(scores):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФТФ",
            course="Физика",
            score=score
        ))

    avg = await repo.average_score_by_faculty("ФТФ")
    assert avg == 85.0


@pytest.mark.asyncio
async def test_repository_average_score_nonexistent_faculty(repo):
    """Test average score for non-existent faculty."""
    avg = await repo.average_score_by_faculty("НЕСУЩЕСТВУЮЩИЙ")
    assert avg == 0.0


@pytest.mark.asyncio
async def test_repository_average_score_single_student(repo):
    """Test average score with single student."""
    await repo.create(StudentCreate(
        last_name="Единственный",
        first_name="Студент",
        faculty="АВТФ",
        course="Механика",
        score=75
    ))

    avg = await repo.average_score_by_faculty("АВТФ")
    assert avg == 75.0


@pytest.mark.asyncio
async def test_repository_average_score_multiple_faculties(repo):
    """Test average score doesn't mix faculties."""
    # ФПМИ students
    await repo.create(StudentCreate(
        last_name="Студент1", first_name="Тест", faculty="ФПМИ", course="Курс", score=100
    ))
    # ФТФ students
    await repo.create(StudentCreate(
        last_name="Студент2", first_name="Тест", faculty="ФТФ", course="Курс", score=50
    ))

    avg_fpmi = await repo.average_score_by_faculty("ФПМИ")
    avg_ftf = await repo.average_score_by_faculty("ФТФ")

    assert avg_fpmi == 100.0
    assert avg_ftf == 50.0


# ===== Students with Low Score Tests =====

@pytest.mark.asyncio
async def test_repository_students_with_low_score(repo):
    """Test getting students with score <= 30."""
    scores = [20, 25, 30, 35, 50, 80]

    for i, score in enumerate(scores):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФПМИ",
            course="Курс",
            score=score
        ))

    low_score_students = await repo.students_with_score()
    assert len(low_score_students) == 3


@pytest.mark.asyncio
async def test_repository_students_with_low_score_none(repo):
    """Test when no students have low score."""
    for i in range(3):
        await repo.create(StudentCreate(
            last_name=f"Студент{i}",
            first_name="Тест",
            faculty="ФПМИ",
            course="Курс",
            score=80 + i
        ))

    low_score_students = await repo.students_with_score()
    assert len(low_score_students) == 0


@pytest.mark.asyncio
async def test_repository_students_with_score_boundary(repo):
    """Test boundary condition for score filter."""
    await repo.create(StudentCreate(
        last_name="Граница",
        first_name="Тест",
        faculty="ФПМИ",
        course="Курс",
        score=30  # Exactly at boundary
    ))

    students = await repo.students_with_score()
    assert len(students) == 1
    assert students[0].score == 30


# ===== Pydantic Schema Tests =====

def test_student_create_schema_valid():
    """Test StudentCreate schema with valid data."""
    student = StudentCreate(
        last_name="Иванов",
        first_name="Иван",
        faculty="ФПМИ",
        course="Информатика",
        score=85
    )
    assert student.last_name == "Иванов"
    assert student.score == 85


def test_student_create_schema_score_boundaries():
    """Test StudentCreate schema score boundaries."""
    # Valid minimum
    student_min = StudentCreate(
        last_name="Тест", first_name="Тест", faculty="Ф", course="К", score=1
    )
    assert student_min.score == 1

    # Valid maximum
    student_max = StudentCreate(
        last_name="Тест", first_name="Тест", faculty="Ф", course="К", score=100
    )
    assert student_max.score == 100


def test_student_create_schema_score_out_of_range():
    """Test StudentCreate schema with score out of range."""
    from pydantic import ValidationError

    # Score below minimum
    with pytest.raises(ValidationError):
        StudentCreate(
            last_name="Тест", first_name="Тест", faculty="Ф", course="К", score=0
        )

    # Score above maximum
    with pytest.raises(ValidationError):
        StudentCreate(
            last_name="Тест", first_name="Тест", faculty="Ф", course="К", score=101
        )


def test_student_create_schema_empty_name():
    """Test StudentCreate schema with empty name."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StudentCreate(
            last_name="", first_name="Тест", faculty="Ф", course="К", score=50
        )


def test_student_create_schema_name_too_long():
    """Test StudentCreate schema with name exceeding max length."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StudentCreate(
            last_name="А" * 101, first_name="Тест", faculty="Ф", course="К", score=50
        )


def test_student_schema_from_attributes():
    """Test Student schema can be created from ORM attributes."""
    from app.schemas.student import Student as StudentSchema

    # Simulate ORM object
    class MockStudent:
        id = 1
        last_name = "Тест"
        first_name = "Тестов"
        faculty = "ФПМИ"
        course = "Курс"
        score = 80

    student = StudentSchema.model_validate(MockStudent())
    assert student.id == 1
    assert student.last_name == "Тест"
