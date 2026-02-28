#!/usr/bin/env python3
"""Test the fine-tuned P2000 model with proper system prompt."""

import sys
import json
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER_PATH = "./p2000-model-mlx"

print("Loading model...")
model, tokenizer = load(MODEL_NAME, adapter_path=ADAPTER_PATH)

system_prompt = open("system_prompt.txt").read().strip()

# Add abbreviation context
try:
    abbrevs = []
    with open("abbreviations.jsonl") as f:
        for line in f:
            if line.strip():
                a = json.loads(line)
                abbrevs.append(f'{a["input"]}={a["output"]}')
    system_prompt += f"\n\nPlaatsnaam-afkortingen: {', '.join(abbrevs)}"
except FileNotFoundError:
    pass

def parse(text):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    sampler = make_sampler(temp=0.1)
    response = generate(model, tokenizer, prompt=prompt, max_tokens=200, sampler=sampler)
    return response

if len(sys.argv) > 1:
    # Single message from command line
    result = parse(" ".join(sys.argv[1:]))
    print(result)
else:
    # Interactive mode
    print("P2000 Parser - type a message (or 'quit' to exit)\n")
    while True:
        try:
            text = input("> ").strip()
            if text.lower() in ("quit", "exit", "q"):
                break
            if text:
                result = parse(text)
                print(result)
                print()
        except (EOFError, KeyboardInterrupt):
            break
