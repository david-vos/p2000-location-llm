# P2000 Location LLM - Fine-tuning Guide

Fine-tune a small language model to extract location data from Dutch P2000 emergency notifications, then run it in **Ollama** or **LM Studio**.

## What it does

Input: `AMBU 17143 2e Opbouwstraat 3076PS Rotterdam ROTTDM bon 33240`

Output:
```json
{"Straatnaam":"2e Opbouwstraat","PlaatsNaam":"Rotterdam","wegnummer":null,"postcode":"3076PS","Regio":"Rotterdam-Rijnmond"}
```

## Requirements

- Python 3.10+
- ~8GB RAM minimum
- GPU recommended (NVIDIA 6GB+ VRAM, or Apple Silicon 8GB+)
- [Ollama](https://ollama.com) installed (for running the model)

## Step 1: Install Python dependencies

```bash
pip install transformers datasets peft trl torch sentencepiece protobuf
```

Apple Silicon users can optionally use MLX (faster training):
```bash
pip install mlx mlx-lm
```

## Step 2: Prepare the training data

```bash
python prepare_data.py
```

Creates `train_chat.jsonl` — your training examples in chat format with the system prompt and abbreviation/region context baked in.

## Step 3: Fine-tune the model

### Option A: PyTorch (NVIDIA GPU / CPU / MPS)

```bash
python finetune.py            # Auto-detects GPU
python finetune.py --cpu      # Force CPU (slow, ~2-4 hours)
```

### Option B: MLX (Apple Silicon, fastest on Mac)

```bash
python finetune_mlx.py
```

### If training was cut short

If you stopped training early (Ctrl+C) but want to use the last saved checkpoint:

```bash
# Fuse the adapter into the base model
python3 -m mlx_lm.fuse --model Qwen/Qwen2.5-1.5B-Instruct --adapter-path build/p2000-model-mlx --save-path build/p2000-model-mlx-fused

# Then continue with Step 4 below
```

## Step 4: Convert to GGUF for Ollama / LM Studio

```bash
python export_gguf.py
```

This:
1. Merges the LoRA weights into the base model
2. Converts to GGUF format (Q8_0 quantization — good quality, small size)
3. Creates an Ollama Modelfile with the system prompt

Output: `./p2000-gguf/p2000-model.gguf` (~1.6GB)

## Step 5a: Run with Ollama

```bash
# Import the model into Ollama
ollama create p2000 -f ./p2000-gguf/Modelfile

# Test it
ollama run p2000 "AMBU 17143 2e Opbouwstraat 3076PS Rotterdam ROTTDM bon 33240"

# Use via API
curl http://localhost:11434/api/generate -d '{
  "model": "p2000",
  "prompt": "AMBU 17143 2e Opbouwstraat 3076PS Rotterdam ROTTDM bon 33240",
  "stream": false
}'
```

## Step 5b: Run with LM Studio

1. Open LM Studio
2. Go to **My Models** → **Import**
3. Select `./p2000-gguf/p2000-model.gguf`
4. In the chat settings, paste the contents of `system_prompt.txt` as the system prompt
5. Chat with the model — send P2000 messages, get JSON back

## Model choice

We use **Qwen2.5-1.5B-Instruct** (~1.5GB). Small, fast, handles structured JSON extraction well after fine-tuning.

| Model | Size | Notes |
|-------|------|-------|
| Qwen2.5-0.5B-Instruct | ~0.5GB | Smallest, less accurate |
| Qwen2.5-1.5B-Instruct | ~1.5GB | Best balance (recommended) |
| SmolLM2-1.7B-Instruct | ~1.7GB | Good alternative |

## Files

| File | Purpose |
|------|---------|
| `train.jsonl` | Training examples (P2000 → JSON) |
| `abbreviations.jsonl` | Place name abbreviation mappings |
| `regions.jsonl` | Region name mappings |
| `system_prompt.txt` | System prompt baked into the model |
| `schema.json` | JSON schema for the output |
| `prepare_data.py` | Converts training data to chat format |
| `finetune.py` | Fine-tuning script (PyTorch) |
| `finetune_mlx.py` | Fine-tuning script (Apple Silicon MLX) |
| `export_gguf.py` | Converts fine-tuned model to GGUF for Ollama/LM Studio |

## Tips for better results

- More training examples = better results (100+ is good, 500+ is great)
- Include edge cases: messages with no location, unusual formatting
- The abbreviation and region mappings are included in the system prompt during training
- After adding new examples, re-run steps 2-4
