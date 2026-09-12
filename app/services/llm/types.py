from dataclasses import dataclass


@dataclass(slots=True)
class LLMUsage:
    model: str

    total_duration_ms: float | None = None
    load_duration_ms: float | None = None

    prompt_tokens: int | None = None
    prompt_duration_ms: float | None = None

    completion_tokens: int | None = None
    completion_duration_ms: float | None = None

    tokens_per_second: float | None = None


@dataclass(slots=True)
class LLMResult:
    content: str
    usage: LLMUsage
