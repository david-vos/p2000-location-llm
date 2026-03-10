#!/usr/bin/env python3
"""Convert train.jsonl + abbreviations/regions into chat-format training data."""

import json
import os
import random

def load_jsonl(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def build_context():
    """Build extra context from abbreviations and regions files."""
    parts = []

    try:
        abbrevs = load_jsonl("abbreviations.jsonl")
        mapping = ", ".join(f'{a["input"]}={a["output"]}' for a in abbrevs)
        parts.append(f"Plaatsnaam-afkortingen: {mapping}")
    except FileNotFoundError:
        pass

    try:
        regions = load_jsonl("regions.jsonl")
        mapping = ", ".join(f'{r["input"]}={r["output"]}' for r in regions)
        parts.append(f"Regio's: {mapping}")
    except FileNotFoundError:
        pass

    return "\n".join(parts)

def augment_entries(entries):
    """Add synthetic variations for key patterns. Returns expanded list."""
    result = list(entries)

    # N Re Place: add variations with different road numbers
    n_place_variants = [
        ("N261 Re Tilburg", {"Straatnaam": None, "PlaatsNaam": "Tilburg", "wegnummer": "N261", "postcode": None, "Regio": None}),
        ("N270 Re Helmond", {"Straatnaam": None, "PlaatsNaam": "Helmond", "wegnummer": "N270", "postcode": None, "Regio": None}),
        ("A12 Re Arnhem", {"Straatnaam": None, "PlaatsNaam": "Arnhem", "wegnummer": "A12", "postcode": None, "Regio": None}),
    ]
    for inp, out in n_place_variants:
        result.append({"input": f"Ongeval wegvervoer letsel {inp}", "output": out})

    # Graag posten + job (non-place)
    for job in ["Havenmeester", "Chauffeur", "Piloot"]:
        result.append({"input": f"Graag posten {job}.", "output": {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None}})

    # Ordinal streets: add 1e, 3e examples
    ordinal_variants = [
        ("AMBU 13112 1e Helmersstraat 1054CX Amsterdam ADAM bon 51234", "1e Helmersstraat", "Amsterdam", "1054CX", "Amsterdam-Amstelland"),
        ("AMBU 17400 3e Oosterparkstraat 1092EA Amsterdam AMSTER bon 35020", "3e Oosterparkstraat", "Amsterdam", "1092EA", "Amsterdam-Amstelland"),
    ]
    for inp, street, city, postcode, regio in ordinal_variants:
        result.append({"input": inp, "output": {"Straatnaam": street, "PlaatsNaam": city, "wegnummer": None, "postcode": postcode, "Regio": regio}})

    return result


def main():
    random.seed(42)
    system_prompt = open("system_prompt.txt").read().strip()
    context = build_context()
    if context:
        system_prompt += "\n\n" + context

    train_data = load_jsonl("train.jsonl")
    if os.path.exists("train_part2.jsonl"):
        train_data.extend(load_jsonl("train_part2.jsonl"))
    # Add edge cases (failing patterns, small variations) - oversample 4x for better learning
    edge_cases = []
    if os.path.exists("train_edge_cases.jsonl"):
        edge_cases = load_jsonl("train_edge_cases.jsonl")
        train_data.extend(edge_cases * 4)  # 4x oversampling for minority patterns

    # Data augmentation: add synthetic variations for key patterns
    train_data = augment_entries(train_data)

    output = []

    for entry in train_data:
        chat = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": entry["input"]},
                {"role": "assistant", "content": json.dumps(entry["output"], ensure_ascii=False)},
            ]
        }
        output.append(chat)

    os.makedirs("build", exist_ok=True)
    with open("build/train_chat.jsonl", "w") as f:
        for item in output:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    n_edge = len(edge_cases) * 4 if edge_cases else 0
    print(f"Created build/train_chat.jsonl with {len(output)} examples" + (f" (+{n_edge} edge-case oversamples)" if n_edge else ""))

if __name__ == "__main__":
    main()
