"""
GLM-OCR PDF to Markdown
pip install pymupdf torch torchvision pillow
pip install "git+https://github.com/huggingface/transformers.git"
"""

import os
import sys
import tempfile
import fitz  # PyMuPDF
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

PDF_PATH = r"c:\Dev\test\document_18917.pdf"
OUTPUT_MD = r"c:\Dev\test\document_18917_ocr.md"
MODEL_PATH = "zai-org/GLM-OCR"
DPI = 200

# Load model
print("Loading GLM-OCR model...")
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,   # half memory vs float32
    device_map=None,              # load directly to CPU, no disk offloading
    low_cpu_mem_usage=True,
)
model.eval()

# Open PDF
doc = fitz.open(PDF_PATH)
total = len(doc)
print(f"PDF has {total} page(s)\n")

results = []

for i in range(total):
    print(f"[{i+1}/{total}] Processing page...", end=" ", flush=True)

    # Render page to image
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = doc[i].get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Save temp image
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, format="PNG")

    # OCR using exact HuggingFace example
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": tmp.name},
                {"type": "text", "text": "Text Recognition:"},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)

    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=8192)

    output_text = processor.decode(
        generated_ids[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )

    os.remove(tmp.name)
    results.append(output_text.strip())
    print("Done")

doc.close()

# Write markdown
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(f"# OCR Output — {os.path.basename(PDF_PATH)}\n\n")
    for i, text in enumerate(results):
        f.write(f"## Page {i+1}\n\n{text}\n\n---\n\n")

print(f"\nSaved to: {OUTPUT_MD}")
