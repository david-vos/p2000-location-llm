#!/usr/bin/env python3
"""Check if test expectations conflict with training data in train.jsonl.

Scans train.jsonl for entries whose input matches a test case input (or
contains key tokens from it), then compares the training output fields
against the test's expected output.  Any mismatch means the model is
being *taught* the wrong answer.
"""

import json
import sys

TRAIN_FILE = "train.jsonl"
FIELDS = ["Straatnaam", "PlaatsNaam", "wegnummer", "postcode", "Regio"]

# Import test cases from test_ollama
from test_ollama import TESTS


def load_training_data(path: str) -> list[dict]:
    entries = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append({"lineno": lineno, **json.loads(line)})
            except json.JSONDecodeError:
                print(f"WARNING: invalid JSON on line {lineno}", file=sys.stderr)
    return entries


def find_conflicts(test: dict, training_data: list[dict]) -> list[dict]:
    """Find training entries that match the test input but have conflicting outputs."""
    conflicts = []
    expected = test["expected"]

    for entry in training_data:
        train_input = entry.get("input", "")
        train_output = entry.get("output", {})

        # Check for exact input match or significant token overlap
        test_tokens = set(test["input"].split())
        train_tokens = set(train_input.split())
        # Skip trivial tokens (numbers, short codes)
        meaningful_test = {t for t in test_tokens if len(t) > 3 and not t.isdigit()}
        meaningful_train = {t for t in train_tokens if len(t) > 3 and not t.isdigit()}

        if not meaningful_test:
            continue

        overlap = meaningful_test & meaningful_train
        overlap_ratio = len(overlap) / len(meaningful_test) if meaningful_test else 0

        if overlap_ratio < 0.5:
            continue

        # Compare output fields — look for values that the training data
        # places in a *different* field than the test expects.
        field_conflicts = []
        for field in FIELDS:
            exp_val = expected.get(field)
            train_val = train_output.get(field)

            if exp_val is None and train_val is None:
                continue

            # Direct field mismatch on the same input
            if test["input"] == train_input and exp_val != train_val:
                field_conflicts.append({
                    "field": field,
                    "test_expected": exp_val,
                    "training_has": train_val,
                    "type": "exact_match",
                })
                continue

            # Value in wrong field: training puts a value in field X,
            # but test expects that same value in field Y
            if train_val is not None and train_val != exp_val:
                # Check if this value belongs in a different field according to test
                for other_field in FIELDS:
                    if other_field == field:
                        continue
                    if expected.get(other_field) == train_val:
                        field_conflicts.append({
                            "field": field,
                            "test_expected": exp_val,
                            "training_has": train_val,
                            "correct_field": other_field,
                            "type": "wrong_field",
                        })
                        break

        if field_conflicts:
            conflicts.append({
                "lineno": entry["lineno"],
                "train_input": train_input,
                "train_output": train_output,
                "field_conflicts": field_conflicts,
            })

    return conflicts


def main():
    training_data = load_training_data(TRAIN_FILE)
    print(f"Loaded {len(training_data)} training entries from {TRAIN_FILE}")
    print(f"Checking {len(TESTS)} test cases...\n")

    total_issues = 0

    for i, test in enumerate(TESTS, 1):
        conflicts = find_conflicts(test, training_data)
        if not conflicts:
            continue

        total_issues += 1
        print(f"--- Test {i}: {test['input'][:70]} ---")
        print(f"  Expected: {json.dumps(test['expected'])}")

        for conflict in conflicts:
            print(f"\n  Training line {conflict['lineno']}: {conflict['train_input']}")
            print(f"  Training output: {json.dumps(conflict['train_output'])}")
            for fc in conflict["field_conflicts"]:
                if fc["type"] == "exact_match":
                    print(f"    CONFLICT [{fc['field']}]: test expects {fc['test_expected']!r}, training has {fc['training_has']!r}")
                else:
                    print(f"    WRONG FIELD [{fc['field']}]: training has {fc['training_has']!r} here, but test expects it in [{fc['correct_field']}]")
        print()

    print(f"{'='*40}")
    if total_issues == 0:
        print("No training data conflicts found.")
        return 0
    else:
        print(f"Found conflicts in {total_issues} test case(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
