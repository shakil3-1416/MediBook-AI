import asyncio
import statistics
import time

from app.services.llm.intent import (
    classify_intent,
)


TESTS = [
    (
        "I'd rather see someone appropriate for recurring numbness, "
        "somewhere convenient for me.",
        "search_doctor",
    ),
    (
        "Is there anyone suitable available tomorrow evening?",
        "check_availability",
    ),
    (
        "Could we move the visit I already arranged to another day?",
        "reschedule_appointment",
    ),
    (
        "I need to get rid of the booking I made earlier.",
        "cancel_appointment",
    ),
]


async def main():

    latencies = []

    correct = 0

    print()
    print("=" * 70)
    print("MEDIBOOK 1B ROUTER BENCHMARK")
    print("=" * 70)

    for text, expected in TESTS:

        started = time.perf_counter()

        try:

            result = await classify_intent(
                text
            )

            elapsed = (
                time.perf_counter()
                - started
            ) * 1000

            latencies.append(
                elapsed
            )

            passed = (
                result.intent
                == expected
            )

            if passed:
                correct += 1

            print()
            print("INPUT:")
            print(text)

            print(
                "EXPECTED:",
                expected,
            )

            print(
                "ACTUAL:",
                result.intent,
            )

            print(
                "CONFIDENCE:",
                result.confidence,
            )

            print(
                "LATENCY:",
                round(elapsed, 2),
                "ms",
            )

            print(
                "RESULT:",
                (
                    "PASS"
                    if passed
                    else "FAIL"
                ),
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - started
            ) * 1000

            print()
            print("INPUT:")
            print(text)

            print(
                "FAILED AFTER:",
                round(elapsed, 2),
                "ms",
            )

            print(
                "ERROR:",
                repr(exc),
            )

    print()
    print("=" * 70)

    print(
        f"Accuracy: {correct}/{len(TESTS)}"
    )

    if latencies:

        print(
            "Mean:",
            round(
                statistics.mean(
                    latencies
                ),
                2,
            ),
            "ms",
        )

        print(
            "Median:",
            round(
                statistics.median(
                    latencies
                ),
                2,
            ),
            "ms",
        )

        print(
            "Max:",
            round(
                max(latencies),
                2,
            ),
            "ms",
        )

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
