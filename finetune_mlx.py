#!/usr/bin/env python3
"""Fine-tune Qwen 2.5 using MLX on Apple Silicon."""

import json
import subprocess
import sys
import os

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "./build/p2000-model-mlx"
EPOCHS = 4
BATCH_SIZE = 2
LEARNING_RATE = 1e-4
LORA_RANK = 16
WARMUP_STEPS = 200

def check_deps():
    try:
        import mlx
        import mlx_lm
        from transformers import AutoTokenizer
    except ImportError:
        print("Installing MLX dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mlx", "mlx-lm", "transformers"])


def prepare_mlx_data(model_name):
    """Convert train_chat.jsonl to MLX-compatible format using Qwen chat template."""
    from transformers import AutoTokenizer

    os.makedirs("build/mlx-data", exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    with open("build/train_chat.jsonl") as f:
        examples = [json.loads(line) for line in f if line.strip()]

    text_examples = []
    for ex in examples:
        text = tokenizer.apply_chat_template(
            ex["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        text_examples.append({"text": text})

    # 90/10 train/valid split
    split = max(1, len(text_examples) - len(text_examples) // 10)
    train = text_examples[:split]
    valid = text_examples[split:]

    # If valid is empty, duplicate last train example
    if not valid:
        valid = [train[-1]]

    for name, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
        with open(f"build/mlx-data/{name}", "w") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"MLX data: {len(train)} train, {len(valid)} valid examples")
    return len(train)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_NAME, help="Base model to fine-tune")
    args = parser.parse_args()

    model_name = args.model
    check_deps()

    if not os.path.exists("build/train_chat.jsonl"):
        print("Run prepare_data.py first!")
        sys.exit(1)

    train_count = prepare_mlx_data(model_name)
    steps_per_epoch = max(1, train_count // BATCH_SIZE)
    total_iters = EPOCHS * steps_per_epoch
    print(f"Training: {EPOCHS} epochs, {steps_per_epoch} steps/epoch, {total_iters} total iters")
    print(f"LR warmup: {WARMUP_STEPS} steps")

    # Create config with LR schedule (warmup + cosine decay)
    decay_steps = max(1, total_iters - WARMUP_STEPS)
    config = {
        "model": model_name,
        "train": True,
        "data": "./build/mlx-data",
        "batch_size": BATCH_SIZE,
        "iters": total_iters,
        "num_layers": LORA_RANK,
        "adapter_path": OUTPUT_DIR,
        "max_seq_length": 4096,
        "grad_checkpoint": True,
        "lora_parameters": {"rank": LORA_RANK, "dropout": 0.0, "scale": 20.0},
        "lr_schedule": {
            "name": "cosine_decay",
            "arguments": [LEARNING_RATE, decay_steps, 1e-6],
            "warmup": WARMUP_STEPS,
            "warmup_init": 0.0,
        },
    }
    config_path = "./build/mlx-train-config.yaml"
    os.makedirs("build", exist_ok=True)
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "-c", config_path,
    ]

    print(f"Fine-tuning {model_name} with MLX...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    # Fuse adapter into model
    fused_dir = "./build/p2000-model-mlx-fused"
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
