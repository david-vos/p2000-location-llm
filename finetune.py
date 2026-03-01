#!/usr/bin/env python3
"""Fine-tune Qwen2.5-1.5B-Instruct on P2000 location extraction."""

import argparse
import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
OUTPUT_DIR = "./build/p2000-model"
EPOCHS = 10
BATCH_SIZE = 4
LEARNING_RATE = 2e-4
MAX_SEQ_LENGTH = 512

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true", help="Train on CPU (slow)")
    parser.add_argument("--model", default=MODEL_NAME, help="Base model to fine-tune")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    args = parser.parse_args()

    device = "cpu" if args.cpu else ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    model_kwargs = {"trust_remote_code": True}
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = "auto"
    elif device == "mps":
        model_kwargs["torch_dtype"] = torch.float32
    else:
        model_kwargs["torch_dtype"] = torch.float32

    print(f"Loading {args.model}...")
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    if device == "cuda":
        model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    if device == "mps":
        model = model.to("mps")

    # Load dataset
    dataset = load_dataset("json", data_files="build/train_chat.jsonl", split="train")

    def format_messages_as_text(messages):
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

    def format_chat(example):
        if tokenizer.chat_template:
            text = tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)
        else:
            text = format_messages_as_text(example["messages"])
        return {"text": text}

    dataset = dataset.map(format_chat)
    print(f"Training on {len(dataset)} examples for {args.epochs} epochs")

    # Training
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=2,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=5,
        save_strategy="epoch",
        fp16=(device == "cuda"),
        bf16=False,
        optim="adamw_torch",
        report_to="none",
        use_cpu=(device == "cpu"),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("Starting training...")
    trainer.train()

    # Save
    print(f"Saving model to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Also merge and save full model for easier inference
    merged_dir = "./build/p2000-model-merged"
    print(f"Merging LoRA weights and saving to {merged_dir}...")
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)

    print("Done! Test with: python inference.py \"your p2000 message here\"")

if __name__ == "__main__":
    main()
