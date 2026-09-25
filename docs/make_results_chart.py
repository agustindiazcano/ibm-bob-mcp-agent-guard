"""Generate a before/after results chart for the docs."""

import json
from pathlib import Path

# Simple ASCII chart — replace with matplotlib if available
BEFORE = {"coverage": 30, "mutation_score": 0, "tests": 3}
AFTER = {"coverage": 85, "mutation_score": 72, "tests": 22}

print("RepoGuard Demo Results")
print("=" * 40)
for key in BEFORE:
    b = BEFORE[key]
    a = AFTER[key]
    bar_b = "█" * (b // 5)
    bar_a = "█" * (a // 5)
    print(f"\n{key}")
    print(f"  Before: {bar_b} {b}")
    print(f"  After:  {bar_a} {a}")
