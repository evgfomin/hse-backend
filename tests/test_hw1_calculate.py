"""
ДЗ 1 — Введение в бэкенд. Асинхронность в Python
Tests for the /calculate/ endpoint that computes squares asynchronously.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from main import app, CalculateRequest, ResultItem, CalculateResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_calculate_single_number(client):
    """Test calculation with a single number."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [5], "delays": [0.1]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["number"] == 5
    assert data["results"][0]["square"] == 25
    assert data["results"][0]["delay"] == 0.1
    assert "total_time" in data
    assert "parallel_faster_than_sequential" in data


@pytest.mark.anyio
async def test_calculate_multiple_numbers(client):
    """Test calculation with multiple numbers."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [2, 3, 4], "delays": [0.1, 0.1, 0.1]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3
    squares = [r["square"] for r in data["results"]]
    assert squares == [4, 9, 16]


@pytest.mark.anyio
async def test_calculate_parallel_faster(client):
    """Test that parallel execution is faster than sequential for multiple items."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [1, 2, 3], "delays": [0.2, 0.2, 0.2]}
    )
    assert response.status_code == 200
    data = response.json()
    # Sequential would take 0.6s, parallel should be ~0.2s
    assert data["parallel_faster_than_sequential"] is True
    assert data["total_time"] < 0.5  # Should be much less than sequential


@pytest.mark.anyio
async def test_calculate_empty_lists(client):
    """Test calculation with empty lists."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [], "delays": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total_time"] >= 0


@pytest.mark.anyio
async def test_calculate_mismatched_lengths(client):
    """Test that mismatched numbers and delays returns validation error."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [1, 2, 3], "delays": [0.1, 0.2]}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_calculate_negative_numbers(client):
    """Test calculation with negative numbers."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [-5, -3], "delays": [0.01, 0.01]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["square"] == 25
    assert data["results"][1]["square"] == 9


@pytest.mark.anyio
async def test_calculate_zero(client):
    """Test calculation with zero."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [0], "delays": [0.01]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["square"] == 0


@pytest.mark.anyio
async def test_calculate_large_numbers(client):
    """Test calculation with large numbers."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [1000, 9999], "delays": [0.01, 0.01]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["square"] == 1000000
    assert data["results"][1]["square"] == 99980001


@pytest.mark.anyio
async def test_calculate_response_structure(client):
    """Test that response has correct structure."""
    response = await client.post(
        "/calculate/",
        json={"numbers": [2], "delays": [0.05]}
    )
    assert response.status_code == 200
    data = response.json()

    # Check top-level keys
    assert "results" in data
    assert "total_time" in data
    assert "parallel_faster_than_sequential" in data

    # Check result item structure
    result = data["results"][0]
    assert "number" in result
    assert "square" in result
    assert "delay" in result
    assert "time" in result


@pytest.mark.anyio
async def test_calculate_time_recorded(client):
    """Test that time is recorded for each computation."""
    delay = 0.1
    response = await client.post(
        "/calculate/",
        json={"numbers": [5], "delays": [delay]}
    )
    assert response.status_code == 200
    data = response.json()
    recorded_time = data["results"][0]["time"]
    # Time should be approximately the delay (with some tolerance)
    assert recorded_time >= delay - 0.05
    assert recorded_time <= delay + 0.1


# Model validation tests
def test_calculate_request_model_valid():
    """Test CalculateRequest model with valid data."""
    request = CalculateRequest(numbers=[1, 2, 3], delays=[0.1, 0.2, 0.3])
    assert request.numbers == [1, 2, 3]
    assert request.delays == [0.1, 0.2, 0.3]


def test_calculate_request_model_mismatched():
    """Test CalculateRequest model with mismatched lengths."""
    with pytest.raises(ValueError, match="same length"):
        CalculateRequest(numbers=[1, 2, 3], delays=[0.1, 0.2])


def test_result_item_model():
    """Test ResultItem model."""
    item = ResultItem(number=5, square=25, delay=0.1, time=0.12)
    assert item.number == 5
    assert item.square == 25
    assert item.delay == 0.1
    assert item.time == 0.12


def test_calculate_response_model():
    """Test CalculateResponse model."""
    results = [ResultItem(number=5, square=25, delay=0.1, time=0.12)]
    response = CalculateResponse(
        results=results,
        total_time=0.12,
        parallel_faster_than_sequential=True
    )
    assert len(response.results) == 1
    assert response.total_time == 0.12
    assert response.parallel_faster_than_sequential is True
