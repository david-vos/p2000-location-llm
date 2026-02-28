#!/usr/bin/env python3
"""Fine-tune using MLX on Apple Silicon. Faster than PyTorch on M-series chips."""

import json
import subprocess
import sys
import os

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
OUTPUT_DIR = "./p2000-model-mlx"
EPOCHS = 10
BATCH_SIZE = 1
LEARNING_RATE = 2e-4
LORA_RANK = 8

def check_deps():
    try:
        import mlx
        import mlx_lm
    except ImportError:
        print("Installing MLX dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mlx", "mlx-lm"])

def format_messages_as_text(messages):
    """Format chat messages as plain text for base models without a chat template."""
    parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            parts.append(f"### System:\n{content}")
        elif role == "user":
            parts.append(f"### User:\n{content}")
        elif role == "assistant":
            parts.append(f"### Assistant:\n{content}")
    return "\n\n".join(parts)

def prepare_mlx_data():
    """Convert train_chat.jsonl to MLX-compatible format (train/valid split)."""
    os.makedirs("mlx-data", exist_ok=True)

    with open("train_chat.jsonl") as f:
        examples = [json.loads(line) for line in f if line.strip()]

    # Convert chat messages to plain text completions
    text_examples = []
    for ex in examples:
        text = format_messages_as_text(ex["messages"])
        text_examples.append({"text": text})

    # 90/10 train/valid split
    split = max(1, len(text_examples) - len(text_examples) // 10)
    train = text_examples[:split]
    valid = text_examples[split:]

    # If valid is empty, duplicate last train example
    if not valid:
        valid = [train[-1]]

    for name, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
        with open(f"mlx-data/{name}", "w") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"MLX data: {len(train)} train, {len(valid)} valid examples")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_NAME, help="Base model to fine-tune")
    args = parser.parse_args()

    model_name = args.model
    check_deps()

    if not os.path.exists("train_chat.jsonl"):
        print("Run prepare_data.py first!")
        sys.exit(1)

    prepare_mlx_data()

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", model_name,
        "--data", "./mlx-data",
        "--train",
        "--batch-size", str(BATCH_SIZE),
        "--num-layers", str(LORA_RANK),
        "--iters", str(EPOCHS * 100),
        "--learning-rate", str(LEARNING_RATE),
        "--adapter-path", OUTPUT_DIR,
        "--grad-checkpoint",
    ]

    print(f"Fine-tuning {model_name} with MLX...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    # Fuse adapter into model
    fused_dir = f"{OUTPUT_DIR}-fused"
    print(f"Fusing adapter weights into {fused_dir}...")
    subprocess.check_call([
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", model_name,
        "--adapter-path", OUTPUT_DIR,
        "--save-path", fused_dir,
    ])

    print(f"Done! Model saved to {fused_dir}")
    print(f'Test with: python inference.py "your p2000 message here"')

if __name__ == "__main__":
    main()
