import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, model_validator

from app.api.appeals import router as appeals_router
from app.api.students import router as student_routers
from app.database import engine, Base
from app.models import student  # noqa: F401 — registers models with Base


class CalculateRequest(BaseModel):
    numbers: list[int]
    delays: list[float]

    @model_validator(mode="after")
    def lengths_match(self):
        if len(self.numbers) != len(self.delays):
            raise ValueError("numbers and delays must have the same length")
        return self


class ResultItem(BaseModel):
    number: int
    square: int
    delay: float
    time: float


class CalculateResponse(BaseModel):
    results: list[ResultItem]
    total_time: float
    parallel_faster_than_sequential: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(appeals_router)
app.include_router(student_routers)

async def compute_square(number: int, delay: float) -> ResultItem:
    start = time.perf_counter()
    await asyncio.sleep(delay)
    square = number * number
    elapsed = time.perf_counter() - start
    return ResultItem(number=number, square=square, delay=delay, time=round(elapsed, 2))


@app.post("/calculate/", response_model=CalculateResponse)
async def calculate(request: CalculateRequest) -> CalculateResponse:
    start_time = time.perf_counter()
    tasks = [compute_square(num, delay) for num, delay in zip(request.numbers, request.delays)]
    results = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_time
    sequential_time = sum(request.delays)
    return CalculateResponse(
        results=list(results),
        total_time=round(total_time, 2),
        parallel_faster_than_sequential=total_time < sequential_time,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)