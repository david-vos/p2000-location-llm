#!/usr/bin/env python3
"""Convert train.jsonl + abbreviations/regions into chat-format training data."""

import json
import os

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

def main():
    system_prompt = open("system_prompt.txt").read().strip()
    context = build_context()
    if context:
        system_prompt += "\n\n" + context

    train_data = load_jsonl("train.jsonl")
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

    print(f"Created build/train_chat.jsonl with {len(output)} examples")

if __name__ == "__main__":
    main()
