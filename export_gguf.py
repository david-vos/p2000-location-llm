#!/usr/bin/env python3
"""Export fine-tuned model to GGUF format for Ollama / LM Studio."""

import os
import subprocess
import sys
import shutil

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
LORA_DIR = "./build/p2000-model"
MLX_FUSED_DIR = "./build/p2000-model-mlx-fused"
MERGED_DIR = "./build/p2000-model-merged"
GGUF_DIR = "./build/p2000-gguf"
GGUF_FILE = os.path.join(GGUF_DIR, "p2000-model.gguf")
QUANTIZATION = "q8_0"

def merge_lora():
    """Merge LoRA adapter into base model."""
    if os.path.exists(MERGED_DIR):
        print(f"Merged model already exists at {MERGED_DIR}, skipping merge.")
        return

    print("Merging LoRA weights into base model...")
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, trust_remote_code=True, torch_dtype=torch.float16
    )
    model = PeftModel.from_pretrained(base_model, LORA_DIR)
    model = model.merge_and_unload()

    model.save_pretrained(MERGED_DIR)
    tokenizer.save_pretrained(MERGED_DIR)
    print(f"Merged model saved to {MERGED_DIR}")

def convert_to_gguf():
    """Convert merged model to GGUF using llama.cpp."""
    os.makedirs(GGUF_DIR, exist_ok=True)

    # Check if llama.cpp convert script is available
    convert_script = None
    for path in [
        os.path.expanduser("~/llama.cpp/convert_hf_to_gguf.py"),
        shutil.which("convert_hf_to_gguf.py"),
        "convert_hf_to_gguf.py",
    ]:
        if path and os.path.exists(path):
            convert_script = path
            break

    if not convert_script:
        # Download convert script from llama.cpp
        local_script = os.path.join(os.path.dirname(__file__) or ".", "convert_hf_to_gguf.py")
        url = "https://raw.githubusercontent.com/ggerganov/llama.cpp/master/convert_hf_to_gguf.py"
        print(f"Downloading convert_hf_to_gguf.py from llama.cpp...")
        try:
            subprocess.check_call(["curl", "-sL", "-o", local_script, url])
            convert_script = local_script
            print("Downloaded successfully.")
        except Exception as e:
            print(f"\nFailed to download converter: {e}")
            print("Please install llama.cpp manually:")
            print("  git clone https://github.com/ggerganov/llama.cpp")
            print("  cd llama.cpp && pip install -r requirements.txt")
            sys.exit(1)

    # Convert HF to GGUF
    raw_gguf = os.path.join(GGUF_DIR, "p2000-model-f16.gguf")
    print(f"Converting to GGUF ({QUANTIZATION})...")

    subprocess.check_call([
        sys.executable, convert_script,
        MERGED_DIR,
        "--outfile", raw_gguf,
        "--outtype", "f16",
    ])

    # Quantize
    llama_quantize = shutil.which("llama-quantize") or os.path.expanduser("~/llama.cpp/llama-quantize")
    if os.path.exists(llama_quantize):
        subprocess.check_call([llama_quantize, raw_gguf, GGUF_FILE, QUANTIZATION])
        os.remove(raw_gguf)
    else:
        # If quantize binary not available, just rename f16
        os.rename(raw_gguf, GGUF_FILE)
        print("Note: llama-quantize not found, saved as f16 (larger file).")

    print(f"GGUF saved to {GGUF_FILE}")

def create_modelfile():
    """Create Ollama Modelfile."""
    system_prompt = open("system_prompt.txt").read().strip()

    # Add abbreviation context
    try:
        import json
        abbrevs = []
        with open("abbreviations.jsonl") as f:
            for line in f:
                if line.strip():
                    a = json.loads(line)
                    abbrevs.append(f'{a["input"]}={a["output"]}')
        system_prompt += f"\n\nPlaatsnaam-afkortingen: {', '.join(abbrevs)}"
    except FileNotFoundError:
        pass

    modelfile = f"""FROM ./p2000-model.gguf

TEMPLATE \"\"\"{{{{- if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{- end }}}}
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"

SYSTEM \"\"\"{system_prompt}\"\"\"

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
PARAMETER num_predict 200
PARAMETER num_ctx 3000
"""

    modelfile_path = os.path.join(GGUF_DIR, "Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(modelfile)

    print(f"Modelfile saved to {modelfile_path}")
    print()
    print("To import into Ollama:")
    print(f"  cd {GGUF_DIR}")
    print("  ollama create p2000 -f Modelfile")
    print()
    print("To test:")
    print('  ollama run p2000 "AMBU 17143 2e Opbouwstraat 3076PS Rotterdam ROTTDM bon 33240"')

def main():
    # Support MLX fused model (already merged, skip LoRA merge step)
    if os.path.exists(MLX_FUSED_DIR):
        print(f"Found MLX fused model at {MLX_FUSED_DIR}")
        if not os.path.exists(MERGED_DIR):
            shutil.copytree(MLX_FUSED_DIR, MERGED_DIR)
            print(f"Copied to {MERGED_DIR}")
    elif not os.path.exists(LORA_DIR) and not os.path.exists(MERGED_DIR):
        print("No fine-tuned model found. Run finetune.py or finetune_mlx.py first!")
        sys.exit(1)
    else:
        merge_lora()

    convert_to_gguf()
    create_modelfile()

if __name__ == "__main__":
    main()
