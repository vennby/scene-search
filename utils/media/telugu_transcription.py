"""
Telugu language support for video transcription and analysis.
Handles Telugu audio, transcription, and translation to English for metadata.
"""

import subprocess
import os
import json
import requests
import time

# ============= CONFIG =============
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5"
TEMPERATURE = 0.3

# ============= LANGUAGE DETECTION =============

def detect_audio_language(video_path):
    """
    Use Whisper to detect the language of audio in the video.
    Returns language code (e.g., 'te' for Telugu, 'en' for English)
    """
    try:
        cmd = [
            r"C:\whisper\whisper-cli.exe",
            "-m", r"C:\whisper\models\ggml-tiny.bin",
            "--detect-language",
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        
        output = result.stdout.strip() + result.stderr.strip()
        
        # Parse language code from output
        # Whisper typically outputs: "Detected language: [lang_code]"
        if "telugu" in output.lower() or "te" in output.lower():
            return "te"
        elif "english" in output.lower() or "en" in output.lower():
            return "en"
        elif "hindi" in output.lower() or "hi" in output.lower():
            return "hi"
        
        # Default to English if detection fails
        return "en"
    
    except Exception as e:
        print(f"Language detection failed: {e}")
        return "en"  # Default to English


def transcribe_video_with_language(video_path, language_code=None):
    """
    Transcribe video with specific language support.
    If language_code is None, auto-detects.
    
    Returns: (transcript_text, language_code, transcript_path)
    """
    # Auto-detect if not specified
    if language_code is None:
        language_code = detect_audio_language(video_path)
        print(f"🔍 Detected language: {language_code}")
    
    # Whisper language codes
    lang_map = {
        "te": "telugu",
        "en": "english",
        "hi": "hindi",
    }
    
    lang_arg = lang_map.get(language_code, "auto")
    
    try:
        cmd = [
            r"C:\whisper\whisper-cli.exe",
            "-m", r"C:\whisper\models\ggml-tiny.bin",
            "--language", lang_arg,
            "-f", video_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=300
        )
        
        transcript = result.stdout.strip()
        
        if not transcript:
            raise RuntimeError(f"Whisper produced no transcript for language: {lang_arg}")
        
        transcript_path = os.path.splitext(video_path)[0] + f"_{language_code}.txt"
        
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        print(f"✓ Transcribed in {language_code}: {len(transcript)} characters")
        return transcript, language_code, transcript_path
    
    except Exception as e:
        print(f"Transcription error: {e}")
        raise


# ============= LANGUAGE-AWARE OLLAMA =============

def ollama(prompt):
    """Call Ollama model with streaming support"""
    try:
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
    
    except Exception as e:
        print(f"Ollama error: {e}")
        return ""


def translate_telugu_to_english(telugu_text):
    """
    Translate Telugu transcript to English for metadata.
    Keeps original Telugu transcript intact.
    
    Returns: English translation
    """
    if not telugu_text:
        return ""
    
    prompt = f"""Translate the following Telugu text to English. Preserve the meaning and context.

TELUGU TEXT:
{telugu_text}

TRANSLATION (English only):"""
    
    translation = ollama(prompt)
    return translation.strip()


def analyze_telugu_transcript(telugu_transcript, language_code="te"):
    """
    Analyze Telugu transcript and generate English metadata.
    
    Returns: {
        "language": "te",
        "original_transcript": "Telugu text...",
        "english_translation": "English translation...",
        "title": "Video Title",
        "description": "English description",
        "tags": ["tag1", "tag2"],
        "summary": "Brief summary in English"
    }
    """
    
    print(f"📝 Analyzing {language_code} transcript...")
    
    # Translate to English for processing
    if language_code == "te":
        english_text = translate_telugu_to_english(telugu_transcript)
        print(f"✓ Translated to English: {len(english_text)} characters")
    else:
        english_text = telugu_transcript
    
    # Generate metadata in English
    analysis_prompt = f"""You are analyzing a video transcript.

TRANSCRIPT:
{english_text[:2000]}  # Limit for efficiency

TASKS:
1. Generate a concise TITLE (max 12 words)
2. Generate a BRIEF SUMMARY (2–3 sentences)
3. Generate 5-7 TAGS (comma-separated, lowercase)

Output as JSON with keys: "title", "summary", "tags"
Output ONLY valid JSON, no other text."""
    
    response = ollama(analysis_prompt)
    
    try:
        # Parse JSON response
        metadata = json.loads(response)
        
        return {
            "language": language_code,
            "original_transcript": telugu_transcript,
            "english_translation": english_text,
            "title": metadata.get("title", "Untitled"),
            "description": metadata.get("summary", ""),
            "tags": ", ".join(metadata.get("tags", [])),
            "summary": metadata.get("summary", "")
        }
    
    except json.JSONDecodeError:
        print(f"⚠ JSON parsing failed, using fallback")
        return {
            "language": language_code,
            "original_transcript": telugu_transcript,
            "english_translation": english_text,
            "title": "Video",
            "description": english_text[:200],
            "tags": "",
            "summary": english_text[:200]
        }


def analyze_mixed_language_transcript(transcript, detected_language=None):
    """
    Handle transcripts that might be in Telugu, English, or mixed.
    Intelligently processes based on detected language.
    
    Returns: analysis dict with language-specific handling
    """
    
    if detected_language is None:
        # Try to detect language from content
        if any(char in transcript for char in 'అఆఇఈఉఊఋఌఎఏఐఒఓఔ'):
            detected_language = "te"
        else:
            detected_language = "en"
    
    print(f"📊 Detected language: {detected_language}")
    
    if detected_language == "te":
        return analyze_telugu_transcript(transcript, "te")
    else:
        # Use standard English analysis
        return analyze_english_transcript(transcript)


def analyze_english_transcript(english_transcript):
    """
    Analyze English transcript (fallback for non-Telugu).
    """
    analysis_prompt = f"""You are analyzing a video transcript.

TRANSCRIPT:
{english_transcript[:2000]}

TASKS:
1. Generate a concise TITLE (max 12 words)
2. Generate a BRIEF SUMMARY (2–3 sentences)
3. Generate 5-7 TAGS (comma-separated, lowercase)

Output as JSON with keys: "title", "summary", "tags"
Output ONLY valid JSON, no other text."""
    
    response = ollama(analysis_prompt)
    
    try:
        metadata = json.loads(response)
        return {
            "language": "en",
            "original_transcript": english_transcript,
            "english_translation": english_transcript,
            "title": metadata.get("title", "Untitled"),
            "description": metadata.get("summary", ""),
            "tags": ", ".join(metadata.get("tags", [])),
            "summary": metadata.get("summary", "")
        }
    except json.JSONDecodeError:
        return {
            "language": "en",
            "original_transcript": english_transcript,
            "english_translation": english_transcript,
            "title": "Video",
            "description": english_transcript[:200],
            "tags": "",
            "summary": english_transcript[:200]
        }
