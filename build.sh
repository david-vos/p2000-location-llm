#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-Qwen/Qwen2.5-1.5B-Instruct}"
BASE_NAME="${2:-p2000}"

# Find next version number by checking existing ollama models
LATEST=$(ollama list 2>/dev/null | grep -o "${BASE_NAME}v[0-9]*" | sed "s/${BASE_NAME}v//" | sort -n | tail -1 || true)
if [ -z "$LATEST" ]; then
  NEXT_VERSION=1
else
  NEXT_VERSION=$((LATEST + 1))
fi
OLLAMA_NAME="${BASE_NAME}v${NEXT_VERSION}"

echo "==> Cleaning build directory..."
rm -rf build

echo "==> Fixing training data (Regio from PlaatsNaam, etc.)..."
python3 fix_training_data.py

echo "==> Preparing training data..."
python3 prepare_data.py

echo "==> Fine-tuning with MLX (model: $MODEL)..."
python3 finetune_mlx.py --model "$MODEL"

echo "==> Exporting to GGUF..."
python3 export_gguf.py

echo "==> Creating ollama model '$OLLAMA_NAME'..."
cd build/p2000-gguf
ollama create "$OLLAMA_NAME" -f Modelfile
cd ../..

echo "==> Done! Run 'python test_ollama.py' to test."
