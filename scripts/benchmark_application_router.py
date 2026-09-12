import asyncio
import statistics
import time

from app.services.llm.router import (
    route_message,
)


TESTS = [
    "What can MediBook do?",
    "What dosage should I take?",
    (
        "Could you find someone who treats heart problems "
        "around Dhanmondi, preferably a woman?"
    ),
    (
        "Is there anyone suitable available "
        "tomorrow evening?"
    ),
    (
        "Could we move the visit I already arranged "
        "to another day?"
    ),
    (
        "I need to get rid of the booking "
        "I made earlier."
    ),
    (
        "I'd rather see someone appropriate for recurring "
        "numbness, somewhere convenient for me."
    ),
]


async def main():

    values = []

    print()
    print("=" * 72)
    print("MEDIBOOK APPLICATION ROUTER BENCHMARK")
    print("=" * 72)

    for message in TESTS:

        started = (
            time.perf_counter()
        )

        result = await route_message(
            message
        )

        ms = (
            time.perf_counter()
            - started
        ) * 1000

        values.append(ms)

        print()
        print("INPUT:")
        print(message)

        print(
            f"SOURCE: {result.source}"
        )

        print(
            f"INTENT: {result.intent}"
        )

        print(
            f"CONFIDENCE: {result.confidence}"
        )

        print(
            f"LATENCY: {ms:.3f} ms"
        )

        print(
            f"ENTITIES: {result.entities}"
        )

    print()
    print("=" * 72)

    print(
        f"Mean:   {statistics.mean(values):.3f} ms"
    )

    print(
        f"Median: {statistics.median(values):.3f} ms"
    )

    print(
        f"Max:    {max(values):.3f} ms"
    )

    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(
        main()
    )
