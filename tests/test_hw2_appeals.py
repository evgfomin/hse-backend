"""
ДЗ 2 — FastAPI и Pydantic
Tests for the /appeals endpoint with Pydantic validation.
"""
import pytest
from datetime import date, datetime
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError

from main import app
from app.api.appeals import Appeal, ProblemTypeEnum


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_appeal_data():
    """Valid appeal data for tests."""
    return {
        "last_name": "Иванов",
        "first_name": "Иван",
        "middle_name": "Иванович",
        "birth_date": "1990-05-15",
        "email": "ivanov@example.com",
        "phone": "+79001234567",
        "problem_types": ["no_connection"],
        "problem_at": "2024-01-15T10:30:00"
    }


# ===== API Endpoint Tests =====

@pytest.mark.anyio
async def test_create_appeal_success(client, valid_appeal_data):
    """Test successful appeal creation."""
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Appeal created"}


@pytest.mark.anyio
async def test_create_appeal_multiple_problems(client, valid_appeal_data):
    """Test appeal with multiple problem types."""
    valid_appeal_data["problem_types"] = ["no_connection", "phone_issue"]
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_appeal_invalid_email(client, valid_appeal_data):
    """Test appeal with invalid email."""
    valid_appeal_data["email"] = "not-an-email"
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_appeal_future_birth_date(client, valid_appeal_data):
    """Test appeal with future birth date."""
    valid_appeal_data["birth_date"] = "2030-01-01"
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_appeal_invalid_phone(client, valid_appeal_data):
    """Test appeal with invalid phone format."""
    valid_appeal_data["phone"] = "abc123"
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_appeal_missing_required_field(client, valid_appeal_data):
    """Test appeal with missing required field."""
    del valid_appeal_data["email"]
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_appeal_empty_problem_types(client, valid_appeal_data):
    """Test appeal with empty problem types list."""
    valid_appeal_data["problem_types"] = []
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_appeal_invalid_problem_type(client, valid_appeal_data):
    """Test appeal with invalid problem type."""
    valid_appeal_data["problem_types"] = ["invalid_type"]
    response = await client.post("/appeals", json=valid_appeal_data)
    assert response.status_code == 422


# ===== Pydantic Model Tests =====

def test_appeal_model_valid():
    """Test Appeal model with valid data."""
    appeal = Appeal(
        last_name="Петров",
        first_name="Петр",
        middle_name="Петрович",
        birth_date=date(1985, 3, 20),
        email="petrov@example.com",
        phone="+79001234567",
        problem_types=[ProblemTypeEnum.no_connection],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert appeal.last_name == "Петров"
    assert appeal.first_name == "Петр"
    assert appeal.phone == "+79001234567"


def test_appeal_model_phone_normalization_10_digits():
    """Test phone normalization for 10-digit numbers starting with 9."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="9001234567",
        problem_types=[ProblemTypeEnum.no_connection],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert appeal.phone == "+79001234567"


def test_appeal_model_phone_normalization_11_digits_with_7():
    """Test phone normalization for 11-digit numbers starting with 7."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="79001234567",
        problem_types=[ProblemTypeEnum.no_connection],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert appeal.phone == "+79001234567"


def test_appeal_model_phone_normalization_11_digits_with_8():
    """Test phone normalization for 11-digit numbers starting with 8."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="89001234567",
        problem_types=[ProblemTypeEnum.no_connection],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert appeal.phone == "+79001234567"


def test_appeal_model_phone_with_plus():
    """Test phone number with plus prefix."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="+79001234567",
        problem_types=[ProblemTypeEnum.no_connection],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert appeal.phone == "+79001234567"


def test_appeal_model_invalid_phone_format():
    """Test Appeal model with invalid phone format."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="Тест",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(1990, 1, 1),
            email="test@example.com",
            phone="invalid",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_phone_too_short():
    """Test Appeal model with phone too short."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="Тест",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(1990, 1, 1),
            email="test@example.com",
            phone="123456",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_future_birth_date():
    """Test Appeal model with future birth date."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="Тест",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(2030, 1, 1),
            email="test@example.com",
            phone="+79001234567",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_today_birth_date():
    """Test Appeal model with today's date as birth date."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="Тест",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date.today(),
            email="test@example.com",
            phone="+79001234567",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_empty_last_name():
    """Test Appeal model with empty last name."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(1990, 1, 1),
            email="test@example.com",
            phone="+79001234567",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_name_too_long():
    """Test Appeal model with name exceeding max length."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="А" * 101,
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(1990, 1, 1),
            email="test@example.com",
            phone="+79001234567",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_invalid_email():
    """Test Appeal model with invalid email."""
    with pytest.raises(ValidationError):
        Appeal(
            last_name="Тест",
            first_name="Тест",
            middle_name="Тестович",
            birth_date=date(1990, 1, 1),
            email="not-an-email",
            phone="+79001234567",
            problem_types=[ProblemTypeEnum.no_connection],
            problem_at=datetime(2024, 1, 15, 10, 30)
        )


def test_appeal_model_multiple_problem_types():
    """Test Appeal model with multiple problem types."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="+79001234567",
        problem_types=[ProblemTypeEnum.no_connection, ProblemTypeEnum.phone_issue],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert len(appeal.problem_types) == 2


def test_appeal_model_all_problem_types():
    """Test Appeal model with all problem types."""
    appeal = Appeal(
        last_name="Тест",
        first_name="Тест",
        middle_name="Тестович",
        birth_date=date(1990, 1, 1),
        email="test@example.com",
        phone="+79001234567",
        problem_types=[
            ProblemTypeEnum.no_connection,
            ProblemTypeEnum.phone_issue,
            ProblemTypeEnum.no_messages
        ],
        problem_at=datetime(2024, 1, 15, 10, 30)
    )
    assert len(appeal.problem_types) == 3


# ===== Enum Tests =====

def test_problem_type_enum_values():
    """Test ProblemTypeEnum values."""
    assert ProblemTypeEnum.no_connection.value == "no_connection"
    assert ProblemTypeEnum.phone_issue.value == "phone_issue"
    assert ProblemTypeEnum.no_messages.value == "mo_messages"  # Note: typo in original


def test_problem_type_enum_from_string():
    """Test creating enum from string."""
    assert ProblemTypeEnum("no_connection") == ProblemTypeEnum.no_connection
    assert ProblemTypeEnum("phone_issue") == ProblemTypeEnum.phone_issue
