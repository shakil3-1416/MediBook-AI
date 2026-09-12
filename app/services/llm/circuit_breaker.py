import time
from dataclasses import dataclass


@dataclass
class LLMCircuitBreaker:
    failure_threshold: int = 3
    recovery_seconds: float = 30.0

    failures: int = 0
    opened_at: float | None = None

    def allow_request(
        self,
    ) -> bool:

        if self.opened_at is None:
            return True

        elapsed = (
            time.monotonic()
            - self.opened_at
        )

        if elapsed >= self.recovery_seconds:
            self.reset()
            return True

        return False

    def record_success(
        self,
    ) -> None:
        self.reset()

    def record_failure(
        self,
    ) -> None:

        self.failures += 1

        if (
            self.failures
            >= self.failure_threshold
        ):
            self.opened_at = (
                time.monotonic()
            )

    def reset(
        self,
    ) -> None:
        self.failures = 0
        self.opened_at = None


llm_circuit_breaker = (
    LLMCircuitBreaker()
)
