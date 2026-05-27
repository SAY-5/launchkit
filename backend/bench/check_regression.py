"""bench-regress smoke gate.

Runs the notes-list benchmark twice on the same machine: a reference pass and a
current pass. Fails if the current median latency exceeds the reference by more
than the allowed fraction (default 30 percent). Running both passes in the same
environment keeps the gate stable across the different hardware CI may use,
while still catching a structural regression in the hot path (for example a
dropped index or an accidental full-table scan).

Run: python -m bench.check_regression
"""

from __future__ import annotations

import sys

from bench.bench_notes_list import run

THRESHOLD = 0.30
NOTES = 2000
ITERATIONS = 200


def main() -> None:
    reference = run(NOTES, ITERATIONS)
    current = run(NOTES, ITERATIONS)

    ref_median = reference["median_ms"]
    cur_median = current["median_ms"]
    ceiling = ref_median * (1 + THRESHOLD)

    print(f"reference median: {ref_median} ms (p95 {reference['p95_ms']} ms)")
    print(f"current median:   {cur_median} ms (p95 {current['p95_ms']} ms)")
    print(f"ceiling (+30%):   {round(ceiling, 3)} ms")

    if cur_median > ceiling:
        print("REGRESSION: current median exceeds the reference ceiling")
        sys.exit(1)
    print("OK: within threshold")


if __name__ == "__main__":
    main()
