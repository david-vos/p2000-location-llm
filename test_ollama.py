#!/usr/bin/env python3
"""Test the P2000 ollama model against known expected outputs."""

import json
import subprocess
import sys

MODELS = ["p2000v13"]

TESTS = [
    {
        "input": "BDH-02 Stank/hind. lucht Roland Holstlaan Delft 155530",
        "expected": {"Straatnaam": "Roland Holstlaan", "PlaatsNaam": "Delft", "wegnummer": None, "postcode": None, "Regio": "Haaglanden"},
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
        "expected": {"Straatnaam": "Maasdijk", "PlaatsNaam": "Rotterdam", "wegnummer": "A20", "postcode": None, "Regio": "Rotterdam-Rijnmond"},
    },
    {
        "input": "Best Rit: 27887",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Best", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "BAD-03 Stank/hind. lucht (gaslucht) (binnen) Langswater Amsterdam 132531",
        "expected": {"Straatnaam": "Langswater", "PlaatsNaam": "Amsterdam", "wegnummer": None, "postcode": None, "Regio": "Amsterdam-Amstelland"},
    },
    {
        "input": "A1 AMBU 17102 Westeinde 2512GR Den Haag SGRAVH bon 32110",
        "expected": {"Straatnaam": "Westeinde", "PlaatsNaam": "Den Haag", "wegnummer": None, "postcode": "2512GR", "Regio": "Haaglanden"},
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
    {
        "input": "12148 Rit 33527 Houtmarkt Haarlem",
        "expected": {"Straatnaam": "Houtmarkt", "PlaatsNaam": "Haarlem", "wegnummer": None, "postcode": None, "Regio": "Kennemerland"},
    },
    {
        "input": "Eindhoven Rit: 27989",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Eindhoven", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "Ambu 07123 VWS Arnhem Rit 68845",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Arnhem", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "Graag posten Brugwachter.",
        "expected": {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "10111 Rit 33526 VWS Wognum Nieuweweg Wognum",
        "expected": {"Straatnaam": "Nieuweweg", "PlaatsNaam": "Wognum", "wegnummer": None, "postcode": None, "Regio": None},
    },
    {
        "input": "AMBU 17104 Boorn 3068LA Rotterdam ROTTDM bon 34589",
        "expected": {"Straatnaam": "Boorn", "PlaatsNaam": "Rotterdam", "wegnummer": None, "postcode": "3068LA", "Regio": "Rotterdam-Rijnmond"},
    },
    {
        "input": "BRT-01 Wateroverlast (flat) Winston Churchilllaan Spijkenisse 179237",
        "expected": {"Straatnaam": "Winston Churchilllaan", "PlaatsNaam": "Spijkenisse", "wegnummer": None, "postcode": None, "Regio": "Rotterdam-Rijnmond"},
    },
    {
        "input": "BON-02 Ongeval wegvervoer Noordelijke Esweg Weijinksweg Hengelo 059096 059333",
        "expected": {"Straatnaam": "Noordelijke Esweg", "PlaatsNaam": "Hengelo", "wegnummer": None, "postcode": None, "Regio": "Twente"},
    },
    {
        "input": "Aanrijding letsel Noordelijke Esweg Weijinksweg Hengelo 156507",
        "expected": {"Straatnaam": "Noordelijke Esweg", "PlaatsNaam": "Hengelo", "wegnummer": None, "postcode": None, "Regio": "Twente"},
    },
    {
        "input": "Obrechtlaan SGRAVH : 15123",
        "expected": {"Straatnaam": "Obrechtlaan", "PlaatsNaam": "Den Haag", "wegnummer": None, "postcode": None, "Regio": "Haaglanden"},
    },
    {
        "input": "Lelystad 37162",
        "expected": {"Straatnaam": None, "PlaatsNaam": "Lelystad", "wegnummer": None, "postcode": None, "Regio": None},
    },
]

FIELDS = ["Straatnaam", "PlaatsNaam", "wegnummer", "postcode", "Regio"]


def query_ollama(model: str, message: str) -> dict:
    result = subprocess.run(
        ["ollama", "run", model, message],
        capture_output=True, text=True, timeout=30,
    )
    raw = result.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw, "_error": "invalid JSON"}


def run_tests_for_model(model: str) -> int:
    """Run all tests for a single model, return number passed."""
    passed = 0
    failed = 0

    print(f"\n{'#'*50}")
    print(f"# Model: {model}")
    print(f"{'#'*50}")

    for i, test in enumerate(TESTS, 1):
        inp = test["input"]
        expected = test["expected"]
        print(f"\n--- Test {i}/{len(TESTS)} ---")
        print(f"Input:    {inp}")

        actual = query_ollama(model, inp)

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

    print(f"\n{model}: {passed}/{len(TESTS)} passed, {failed} failed")
    return passed


def main():
    results = {}
    for model in MODELS:
        results[model] = run_tests_for_model(model)

    print(f"\n{'='*50}")
    print(f"FINAL REPORT")
    print(f"{'='*50}")
    for model, passed in sorted(results.items(), key=lambda x: x[1], reverse=True):
        pct = passed / len(TESTS) * 100
        print(f"  {model:<20} {passed}/{len(TESTS)} ({pct:.0f}%)")

    best = max(results, key=results.get)
    if len(MODELS) > 1:
        print(f"\nBest model: {best} ({results[best]}/{len(TESTS)})")

    return 0 if all(p == len(TESTS) for p in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
