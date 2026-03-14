#!/bin/bash
set -e

VERSION="$1"
GGUF_DIR="build/p2000-gguf"
INPUT_GGUF="${GGUF_DIR}/p2000-model.gguf"
QUANT_GGUF="${GGUF_DIR}/p2000-model-q4_k_m.gguf"
LLAMA_CPP_DIR="build/llama.cpp"

if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh v0.5.5"
  exit 1
fi

if [ ! -f "$INPUT_GGUF" ]; then
  echo "Error: ${INPUT_GGUF} not found. Run export_gguf.py first."
  exit 1
fi

# Ensure llama-quantize is available
LLAMA_QUANTIZE=$(command -v llama-quantize 2>/dev/null || true)
if [ -z "$LLAMA_QUANTIZE" ]; then
  LLAMA_QUANTIZE="${LLAMA_CPP_DIR}/llama-quantize"
fi
if [ ! -x "$LLAMA_QUANTIZE" ]; then
  LLAMA_QUANTIZE="${HOME}/llama.cpp/llama-quantize"
fi
if [ ! -x "$LLAMA_QUANTIZE" ]; then
  echo "Building llama.cpp for quantization..."
  if [ ! -d "$LLAMA_CPP_DIR" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
  fi
  if [ -f "${LLAMA_CPP_DIR}/CMakeLists.txt" ]; then
    cmake -B "${LLAMA_CPP_DIR}/build" -S "$LLAMA_CPP_DIR" -DGGUF_BUILD_TESTS=OFF -DGGUF_BUILD_EXAMPLES=OFF
    cmake --build "${LLAMA_CPP_DIR}/build" --target llama-quantize
    if [ -x "${LLAMA_CPP_DIR}/build/bin/llama-quantize" ]; then
      LLAMA_QUANTIZE="${LLAMA_CPP_DIR}/build/bin/llama-quantize"
    elif [ -x "${LLAMA_CPP_DIR}/build/llama-quantize" ]; then
      LLAMA_QUANTIZE="${LLAMA_CPP_DIR}/build/llama-quantize"
    fi
  else
    make -C "$LLAMA_CPP_DIR" llama-quantize
    LLAMA_QUANTIZE="${LLAMA_CPP_DIR}/llama-quantize"
  fi
fi
if [ ! -x "$LLAMA_QUANTIZE" ]; then
  echo "Error: could not find or build llama-quantize"
  exit 1
fi

echo "Quantizing to Q4_K_M..."
"$LLAMA_QUANTIZE" "$INPUT_GGUF" "$QUANT_GGUF" q4_k_m
rm -f "$INPUT_GGUF"

echo "Updating Modelfile..."
sed -i.bak 's|FROM ./p2000-model.gguf|FROM ./p2000-model-q4_k_m.gguf|' "${GGUF_DIR}/Modelfile"
rm -f "${GGUF_DIR}/Modelfile.bak"

ZIP_NAME="p2000-model-${VERSION}"
echo "Creating split zip..."
rm -f ${ZIP_NAME}.zip ${ZIP_NAME}.z[0-9]*
zip -s 1900m -r "${ZIP_NAME}.zip" "${GGUF_DIR}/"

ASSETS="${ZIP_NAME}.zip"
for part in ${ZIP_NAME}.z[0-9]*; do
  [ -f "$part" ] && ASSETS="$ASSETS $part"
done

NOTES="## Download & Extract

\`\`\`bash
VERSION=\$(gh release view --repo david-vos/p2000-location-llm --json tagName -q .tagName) && \\
gh release download \"\$VERSION\" --repo david-vos/p2000-location-llm --dir . && \\
zip -s 0 \"p2000-model-\${VERSION}.zip\" --out \"p2000-model-\${VERSION}-combined.zip\" && \\
unzip \"p2000-model-\${VERSION}-combined.zip\" && \\
rm p2000-model-\${VERSION}.z* p2000-model-\${VERSION}-combined.zip
\`\`\`"

echo "Creating GitHub release ${VERSION}..."
gh release create "$VERSION" $ASSETS --title "$VERSION" --notes "$NOTES"

echo "Cleaning up zip files..."
rm -f ${ZIP_NAME}.zip ${ZIP_NAME}.z[0-9]*

echo "Done! Release ${VERSION} created."
