#!/usr/bin/env python3
"""Test the P2000 ollama model against known expected outputs."""

import json
import subprocess
import sys

MODEL = "p2000"

TESTS = [
    {
        "input": "BDH-02 Stank/hind. lucht Roland Holstlaan Delft 155530",
        "expected": {"Straatnaam": "Roland Holstlaan", "PlaatsNaam": "Delft", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "TESTOPROEP MOB",
        "expected": {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "AMBU 17143 2e Opbouwstraat 3076PS Rotterdam ROTTDM bon 33240",
        "expected": {"Straatnaam": "2e Opbouwstraat", "PlaatsNaam": "Rotterdam", "wegnummer": None, "postcode": "3076PS", "Regio": "Rotterdam-Rijnmond"},
    },
    {
        "input": "P 2 BON-04 Buitenbrand Maasdijk A20 Li 34,2 Rotterdam 073421",
        "expected": {"Straatnaam": "Maasdijk", "PlaatsNaam": "Rotterdam", "wegnummer": "A20", "postcode": None, "Regio": None},
    },
    {
        "input": "Best Rit: 27887",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Best", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "BAD-03 Stank/hind. lucht (gaslucht) (binnen) Langswater Amsterdam 132531",
        "expected": {"Straatnaam": "Langswater", "PlaatsNaam": "Amsterdam", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "A1 AMBU 17102 Westeinde 2512GR Den Haag SGRAVH bon 32110",
        "expected": {"Straatnaam": "Westeinde", "PlaatsNaam": "Den Haag", "wegnummer": None, "postcode": "2512GR", "Regio": "'s-Gravenhage"},
    },
    {
        "input": "Ongeval wegvervoer letsel N279 Re Veghel",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Veghel", "wegnummer": "N279", "postcode": None, "Regio": None},
    },
    {
        "input": "Graag verzorging opstarten voor 20 pers",
        "expected": {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "BMD-01 Ass. Politie (OVD-B) (Team Digitale Verkenning) Uilenboslaan Vleuten 099189",
        "expected": {"Straatnaam": "Uilenboslaan", "PlaatsNaam": "Vleuten", "wegnummer": None, "postcode": None, "Regio": None},
    },
]

FIELDS = ["Straatnaam", "PlaatsNaam", "wegnummer", "postcode", "Regio"]


def query_ollama(message: str) -> dict:
    result = subprocess.run(
        ["ollama", "run", MODEL, message],
        capture_output=True, text=True, timeout=30,
    )
    raw = result.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw, "_error": "invalid JSON"}


def main():
    passed = 0
    failed = 0

    for i, test in enumerate(TESTS, 1):
        inp = test["input"]
        expected = test["expected"]
        print(f"\n--- Test {i}/{len(TESTS)} ---")
        print(f"Input:    {inp}")

        actual = query_ollama(inp)

        if "_error" in actual:
            print(f"ERROR:    {actual['_raw']}")
            failed += 1
            continue

        test_passed = True
        for field in FIELDS:
            exp = expected.get(field)
            act = actual.get(field)
            if exp != act:
                print(f"  FAIL {field}: expected {exp!r}, got {act!r}")
                test_passed = False

        if test_passed:
            print(f"  PASS")
            passed += 1
        else:
            print(f"Expected: {json.dumps(expected)}")
            print(f"Actual:   {json.dumps(actual)}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{len(TESTS)} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
