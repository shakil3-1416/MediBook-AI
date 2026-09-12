import asyncio
import statistics
import time

from app.services.llm.fast_router import (
    fast_route,
)

from app.services.llm.gateway import (
    llm_gateway,
)

from app.services.llm.intent import (
    classify_intent,
)


TESTS = [
    (
        "Hello",
        "greeting",
    ),
    (
        "Find me a female cardiologist in Dhanmondi",
        "search_doctor",
    ),
    (
        "Show Dr. Farhana's availability tomorrow",
        "check_availability",
    ),
    (
        "Book the 6 PM slot",
        "book_appointment",
    ),
    (
        "What appointments do I have?",
        "list_appointments",
    ),
    (
        "Cancel my appointment",
        "cancel_appointment",
    ),
    (
        "Move my appointment to tomorrow at 7 PM",
        "reschedule_appointment",
    ),
    (
        "What medicine should I take for chest pain?",
        "medical_request",
    ),
]


async def main() -> None:

    print()
    print(
        "=" * 64
    )
    print(
        "MEDIBOOK LLM PERFORMANCE BENCHMARK"
    )
    print(
        "=" * 64
    )

    healthy = (
        await llm_gateway.health()
    )

    print(
        f"\nOllama health: {healthy}"
    )

    if not healthy:
        raise SystemExit(
            "Ollama is unavailable."
        )

    print(
        "\nWarming model..."
    )

    started = (
        time.perf_counter()
    )

    await llm_gateway.warmup()

    warm_ms = (
        time.perf_counter()
        - started
    ) * 1000

    print(
        f"Warmup: {warm_ms:.1f} ms"
    )

    print()
    print(
        "=" * 64
    )
    print(
        "TIER-0 FAST ROUTER"
    )
    print(
        "=" * 64
    )

    fast_tests = [
        "Hello",
        "What can MediBook do?",
        "How can you help?",
    ]

    for message in fast_tests:

        started = (
            time.perf_counter()
        )

        result = fast_route(
            message
        )

        elapsed = (
            time.perf_counter()
            - started
        ) * 1000

        print(
            f"\nInput: {message}"
        )

        print(
            f"Matched: {result.matched}"
        )

        print(
            f"Route: {result.route}"
        )

        print(
            f"Latency: {elapsed:.3f} ms"
        )

    print()
    print(
        "=" * 64
    )
    print(
        "STRUCTURED INTENT MODEL"
    )
    print(
        "=" * 64
    )

    latencies = []

    correct = 0

    for (
        message,
        expected,
    ) in TESTS:

        started = (
            time.perf_counter()
        )

        intent = (
            await classify_intent(
                message
            )
        )

        elapsed = (
            time.perf_counter()
            - started
        ) * 1000

        latencies.append(
            elapsed
        )

        passed = (
            intent.intent
            == expected
        )

        if passed:
            correct += 1

        print()
        print(
            f"Input: {message}"
        )

        print(
            f"Expected: {expected}"
        )

        print(
            f"Actual:   {intent.intent}"
        )

        print(
            "Result:",
            (
                "PASS"
                if passed
                else "FAIL"
            ),
        )

        print(
            f"Confidence: "
            f"{intent.confidence:.3f}"
        )

        print(
            f"Latency: {elapsed:.1f} ms"
        )

        print(
            "Fields:",
            intent.model_dump(
                exclude={
                    "intent",
                    "confidence",
                }
            ),
        )

    accuracy = (
        correct
        / len(TESTS)
    ) * 100

    print()
    print(
        "=" * 64
    )
    print(
        "INTENT SUMMARY"
    )
    print(
        "=" * 64
    )

    print(
        f"Accuracy: "
        f"{correct}/{len(TESTS)} "
        f"({accuracy:.1f}%)"
    )

    print(
        f"Mean latency: "
        f"{statistics.mean(latencies):.1f} ms"
    )

    print(
        f"Median latency: "
        f"{statistics.median(latencies):.1f} ms"
    )

    print(
        f"Maximum latency: "
        f"{max(latencies):.1f} ms"
    )

    print()
    print(
        "=" * 64
    )
    print(
        "GENERATION PERFORMANCE"
    )
    print(
        "=" * 64
    )

    result = (
        await llm_gateway.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MediBook. "
                        "Answer briefly and only "
                        "describe doctor appointment "
                        "features."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Explain how you can "
                        "help me."
                    ),
                },
            ],
            temperature=0.1,
            num_predict=100,
        )
    )

    print()
    print(
        result.content
    )

    usage = result.usage

    print()
    print(
        "Model:",
        usage.model,
    )

    print(
        "Total duration:",
        usage.total_duration_ms,
        "ms",
    )

    print(
        "Load duration:",
        usage.load_duration_ms,
        "ms",
    )

    print(
        "Prompt tokens:",
        usage.prompt_tokens,
    )

    print(
        "Prompt eval:",
        usage.prompt_duration_ms,
        "ms",
    )

    print(
        "Completion tokens:",
        usage.completion_tokens,
    )

    print(
        "Generation:",
        usage.completion_duration_ms,
        "ms",
    )

    if (
        usage.tokens_per_second
        is not None
    ):
        print(
            "Generation speed:",
            f"{usage.tokens_per_second:.2f}",
            "tokens/sec",
        )

    print()
    print(
        "=" * 64
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
