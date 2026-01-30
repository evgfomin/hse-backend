"""
ДЗ 5 — REST API. Реализация CRUD
Tests for CRUD endpoints: Create, Read, Update, Delete.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def test_db():
    """Create test database engine and session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create test client with test database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def student_data():
    """Valid student data for tests."""
    return {
        "last_name": "Иванов",
        "first_name": "Иван",
        "faculty": "ФПМИ",
        "course": "Информатика",
        "score": 85
    }


# ===== CREATE Tests =====

@pytest.mark.anyio
async def test_create_student_success(client, student_data):
    """Test successful student creation."""
    response = await client.post("/students", json=student_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["last_name"] == "Иванов"
    assert data["first_name"] == "Иван"
    assert data["faculty"] == "ФПМИ"
    assert data["course"] == "Информатика"
    assert data["score"] == 85


@pytest.mark.anyio
async def test_create_student_with_min_score(client):
    """Test creating student with minimum score."""
    response = await client.post("/students", json={
        "last_name": "Тест",
        "first_name": "Тест",
        "faculty": "Ф",
        "course": "К",
        "score": 1
    })
    assert response.status_code == 200
    assert response.json()["score"] == 1


@pytest.mark.anyio
async def test_create_student_with_max_score(client):
    """Test creating student with maximum score."""
    response = await client.post("/students", json={
        "last_name": "Тест",
        "first_name": "Тест",
        "faculty": "Ф",
        "course": "К",
        "score": 100
    })
    assert response.status_code == 200
    assert response.json()["score"] == 100


@pytest.mark.anyio
async def test_create_student_invalid_score_low(client):
    """Test creating student with score below minimum."""
    response = await client.post("/students", json={
        "last_name": "Тест",
        "first_name": "Тест",
        "faculty": "Ф",
        "course": "К",
        "score": 0
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_student_invalid_score_high(client):
    """Test creating student with score above maximum."""
    response = await client.post("/students", json={
        "last_name": "Тест",
        "first_name": "Тест",
        "faculty": "Ф",
        "course": "К",
        "score": 101
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_student_empty_name(client):
    """Test creating student with empty name."""
    response = await client.post("/students", json={
        "last_name": "",
        "first_name": "Тест",
        "faculty": "Ф",
        "course": "К",
        "score": 50
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_student_missing_field(client):
    """Test creating student with missing required field."""
    response = await client.post("/students", json={
        "last_name": "Тест",
        "first_name": "Тест",
        "faculty": "Ф"
        # Missing course and score
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_student_cyrillic_names(client):
    """Test creating student with Cyrillic names."""
    response = await client.post("/students", json={
        "last_name": "Козлов",
        "first_name": "Владимир",
        "faculty": "АВТФ",
        "course": "Теоретическая механика",
        "score": 78
    })
    assert response.status_code == 200
    data = response.json()
    assert data["last_name"] == "Козлов"
    assert data["first_name"] == "Владимир"


# ===== READ Tests =====

@pytest.mark.anyio
async def test_get_all_students_empty(client):
    """Test getting all students when database is empty."""
    response = await client.get("/students")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_all_students(client, student_data):
    """Test getting all students."""
    # Create multiple students
    for i in range(3):
        data = student_data.copy()
        data["last_name"] = f"Студент{i}"
        await client.post("/students", json=data)

    response = await client.get("/students")
    assert response.status_code == 200
    students = response.json()
    assert len(students) == 3


@pytest.mark.anyio
async def test_get_student_by_id(client, student_data):
    """Test getting student by ID."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    student_id = create_response.json()["id"]

    # Get by ID
    response = await client.get(f"/students/{student_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["last_name"] == "Иванов"


@pytest.mark.anyio
async def test_get_student_not_found(client):
    """Test getting non-existent student."""
    response = await client.get("/students/99999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_student_invalid_id(client):
    """Test getting student with invalid ID format."""
    response = await client.get("/students/invalid")
    assert response.status_code == 422


# ===== UPDATE Tests =====

@pytest.mark.anyio
async def test_update_student_success(client, student_data):
    """Test successful student update."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    student_id = create_response.json()["id"]

    # Update student
    updated_data = student_data.copy()
    updated_data["score"] = 95
    updated_data["faculty"] = "ФТФ"

    response = await client.put(f"/students/{student_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 95
    assert data["faculty"] == "ФТФ"


@pytest.mark.anyio
async def test_update_student_all_fields(client, student_data):
    """Test updating all student fields."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    student_id = create_response.json()["id"]

    # Update all fields
    new_data = {
        "last_name": "Петров",
        "first_name": "Петр",
        "faculty": "РЭФ",
        "course": "Электроника",
        "score": 92
    }

    response = await client.put(f"/students/{student_id}", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["last_name"] == "Петров"
    assert data["first_name"] == "Петр"
    assert data["faculty"] == "РЭФ"
    assert data["course"] == "Электроника"
    assert data["score"] == 92


@pytest.mark.anyio
async def test_update_student_not_found(client, student_data):
    """Test updating non-existent student."""
    response = await client.put("/students/99999", json=student_data)
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_student_invalid_data(client, student_data):
    """Test updating student with invalid data."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    student_id = create_response.json()["id"]

    # Try to update with invalid score
    invalid_data = student_data.copy()
    invalid_data["score"] = 150

    response = await client.put(f"/students/{student_id}", json=invalid_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_preserves_id(client, student_data):
    """Test that update preserves original ID."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    original_id = create_response.json()["id"]

    # Update student
    updated_data = student_data.copy()
    updated_data["score"] = 99

    response = await client.put(f"/students/{original_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["id"] == original_id


# ===== DELETE Tests =====

@pytest.mark.anyio
async def test_delete_student_success(client, student_data):
    """Test successful student deletion."""
    # Create student
    create_response = await client.post("/students", json=student_data)
    student_id = create_response.json()["id"]

    # Delete student
    response = await client.request("DELETE", "/students", json=[student_id])
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify deletion
    get_response = await client.get(f"/students/{student_id}")
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_multiple_students(client, student_data):
    """Test deleting multiple students."""
    # Create students
    ids = []
    for i in range(3):
        data = student_data.copy()
        data["last_name"] = f"Студент{i}"
        create_response = await client.post("/students", json=data)
        ids.append(create_response.json()["id"])

    # Delete all
    response = await client.request("DELETE", "/students", json=ids)
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify all deleted
    for student_id in ids:
        get_response = await client.get(f"/students/{student_id}")
        assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_empty_list(client):
    """Test deleting with empty list."""
    response = await client.request("DELETE", "/students", json=[])
    # Should succeed with empty list (no-op)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_delete_partial_existing(client, student_data):
    """Test deleting list with some non-existent IDs."""
    # Create one student
    create_response = await client.post("/students", json=student_data)
    existing_id = create_response.json()["id"]

    # Try to delete existing + non-existent
    response = await client.request("DELETE", "/students", json=[existing_id, 99999])
    # Should still succeed (deletes what exists)
    assert response.status_code == 200


# ===== Response Structure Tests =====

@pytest.mark.anyio
async def test_student_response_structure(client, student_data):
    """Test that student response has correct structure."""
    response = await client.post("/students", json=student_data)
    data = response.json()

    assert "id" in data
    assert "last_name" in data
    assert "first_name" in data
    assert "faculty" in data
    assert "course" in data
    assert "score" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["score"], int)


@pytest.mark.anyio
async def test_students_list_response_structure(client, student_data):
    """Test that students list response has correct structure."""
    # Create students
    await client.post("/students", json=student_data)

    response = await client.get("/students")
    data = response.json()

    assert isinstance(data, list)
    if data:
        student = data[0]
        assert "id" in student
        assert "last_name" in student


# ===== CRUD Flow Tests =====

@pytest.mark.anyio
async def test_full_crud_flow(client):
    """Test complete CRUD flow."""
    # CREATE
    create_data = {
        "last_name": "Тестов",
        "first_name": "Тест",
        "faculty": "ФПМИ",
        "course": "Тестирование",
        "score": 80
    }
    create_response = await client.post("/students", json=create_data)
    assert create_response.status_code == 200
    student_id = create_response.json()["id"]

    # READ
    read_response = await client.get(f"/students/{student_id}")
    assert read_response.status_code == 200
    assert read_response.json()["last_name"] == "Тестов"

    # UPDATE
    update_data = create_data.copy()
    update_data["score"] = 95
    update_response = await client.put(f"/students/{student_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["score"] == 95

    # DELETE
    delete_response = await client.request("DELETE", "/students", json=[student_id])
    assert delete_response.status_code == 200

    # Verify deleted
    verify_response = await client.get(f"/students/{student_id}")
    assert verify_response.status_code == 404


@pytest.mark.anyio
async def test_create_read_multiple(client):
    """Test creating and reading multiple students."""
    # Create 5 students
    created_ids = []
    for i in range(5):
        response = await client.post("/students", json={
            "last_name": f"Студент{i}",
            "first_name": "Тест",
            "faculty": f"Факультет{i % 2}",
            "course": f"Курс{i % 3}",
            "score": 60 + i * 5
        })
        created_ids.append(response.json()["id"])

    # Read all
    all_response = await client.get("/students")
    assert len(all_response.json()) == 5

    # Read each individually
    for student_id in created_ids:
        response = await client.get(f"/students/{student_id}")
        assert response.status_code == 200
