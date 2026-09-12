import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field


@dataclass(slots=True)
class RequestMetrics:
    stages: dict[str, float] = field(
        default_factory=dict
    )

    def add(
        self,
        name: str,
        milliseconds: float,
    ) -> None:
        self.stages[name] = round(
            milliseconds,
            2,
        )


@asynccontextmanager
async def measure_stage(
    metrics: RequestMetrics,
    name: str,
):
    started = time.perf_counter()

    try:
        yield
    finally:
        elapsed = (
            time.perf_counter()
            - started
        ) * 1000

        metrics.add(
            name,
            elapsed,
        )
