import json
import os
import requests
import time

# Function to generate title, summary, and tags from text documents (TXT/PDF)

# =============== CONFIG =============== #

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5"

MAX_CHARS_PER_CHUNK = 4000
TEMPERATURE = 0.3

# =============== UTILITIES =============== #

def load_text_file(path):
    """Load text from a .txt file"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def extract_text_from_pdf(path):
    """Extract text from a PDF file"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    text = []
    with open(path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text())
    
    return "\n".join(text).strip()

def chunk_text(text, max_chars=4000):
    """Split text into manageable chunks without breaking sentences"""
    chunks = []
    while text:
        chunk = text[:max_chars]
        last_period = chunk.rfind(".")
        if last_period != -1:
            chunk = chunk[:last_period + 1]
        chunks.append(chunk.strip())
        text = text[len(chunk):]
    return chunks

# =============== OLLAMA (STREAMING SAFE) =============== #

def ollama(prompt):
    """Call Ollama API with streaming enabled"""
    with requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": TEMPERATURE
            }
        },
        stream=True,
        timeout=None
    ) as r:
        r.raise_for_status()
        output = []

        for line in r.iter_lines():
            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            if "error" in data:
                raise RuntimeError(data["error"])

            if "message" in data and "content" in data["message"]:
                output.append(data["message"]["content"])

            if "response" in data:
                output.append(data["response"])

        return "".join(output)

# =============== SUMMARIZATION =============== #

def summarize_chunk(chunk, idx, total):
    """Summarize a single text chunk"""
    print(f"→ Summarizing chunk {idx}/{total}")
    prompt = f"""
Summarize the following text segment in 2–3 concise sentences.

TEXT:
{chunk}
"""
    return ollama(prompt)

def analyze_and_format(text):
    """
    Analyze and format text into title, description, and tags.
    This is the core function used by both text and PDF summarizers.
    """
    chunks = chunk_text(text, MAX_CHARS_PER_CHUNK)
    summaries = []

    for i, chunk in enumerate(chunks, 1):
        summaries.append(summarize_chunk(chunk, i, len(chunks)))
        time.sleep(0.3)  # gentle pacing for local CPU

    combined = "\n".join(summaries)

    final_prompt = f"""
You are analyzing a document.

TASKS:
1. Generate a concise TITLE (max 12 words)
2. Generate a BRIEF SUMMARY (2–3 sentences)
3. Generate 6–10 TAGS suitable for document search

Rules:
- Output must be in English
- Tags should be lowercase
- Use single or two-word tags only

Return STRICT JSON ONLY:
{{
  "title": "string",
  "summary": "string",
  "tags": ["string"]
}}

CONTENT:
{combined}
"""

    raw = ollama(final_prompt)

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start == -1 or end == -1:
        raise RuntimeError(f"No JSON found in model output:\n{raw}")

    return json.loads(raw[start:end])

# =============== PUBLIC FUNCTIONS =============== #

def summarize_text_file(file_path):
    """Summarize a text file and generate title, description, and tags"""
    text = load_text_file(file_path)
    return analyze_and_format(text)

def summarize_pdf_file(file_path):
    """Extract text from PDF, summarize it, and generate title, description, and tags"""
    text = extract_text_from_pdf(file_path)
    return analyze_and_format(text)