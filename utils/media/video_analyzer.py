"""
Video content analysis without transcription
Analyzes video based on visual features like brightness, motion, scene changes
"""
import cv2
import numpy as np
import json
import requests
import time

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5"
TEMPERATURE = 0.3


def extract_video_features(video_path, sample_frames=5):
    """
    Extract visual features from video without audio
    Returns dict with analyzed features
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration_seconds = total_frames / fps if fps > 0 else 0
        
        # Sample frames at intervals
        frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
        
        brightness_values = []
        motion_levels = []
        color_dominance = []
        prev_frame = None
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Brightness analysis
            brightness = np.mean(gray)
            brightness_values.append(brightness)
            
            # Motion detection using optical flow
            if prev_frame is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2).mean()
                motion_levels.append(magnitude)
            
            # Color analysis
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hue_hist = cv2.calcHist([hsv], [0], None, [256], [0, 256])
            dominant_hue = np.argmax(hue_hist)
            color_dominance.append(int(dominant_hue))
            
            prev_frame = gray
        
        cap.release()
        
        # Analyze collected data
        avg_brightness = np.mean(brightness_values) if brightness_values else 128
        brightness_consistency = np.std(brightness_values) if len(brightness_values) > 1 else 0
        avg_motion = np.mean(motion_levels) if motion_levels else 0
        
        # Classify characteristics
        characteristics = []
        
        if avg_brightness > 150:
            characteristics.append("well-lit")
        elif avg_brightness < 100:
            characteristics.append("dark/dimly-lit")
        else:
            characteristics.append("normally-lit")
        
        if brightness_consistency > 30:
            characteristics.append("varying brightness")
        else:
            characteristics.append("consistent lighting")
        
        if avg_motion > 5:
            characteristics.append("high motion/action")
        elif avg_motion > 2:
            characteristics.append("moderate movement")
        else:
            characteristics.append("static/calm")
        
        # Dominant color classification
        if 0 <= avg(color_dominance) <= 30:
            characteristics.append("red/warm tones")
        elif 31 <= avg(color_dominance) <= 90:
            characteristics.append("yellow/green tones")
        elif 91 <= avg(color_dominance) <= 150:
            characteristics.append("blue/cool tones")
        
        return {
            "duration_seconds": round(duration_seconds, 2),
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "avg_brightness": round(avg_brightness, 2),
            "brightness_consistency": round(brightness_consistency, 2),
            "avg_motion": round(avg_motion, 2),
            "characteristics": characteristics
        }
    
    except Exception as e:
        print(f"Error extracting video features: {e}")
        return {
            "error": str(e),
            "characteristics": ["unable to analyze video"]
        }


def avg(values):
    """Helper to calculate average"""
    return sum(values) / len(values) if values else 0


def ollama(prompt):
    """Send prompt to Ollama and get response"""
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
        print(f"Ollama request failed: {e}")
        raise


def analyze_video_content(video_path):
    """
    Analyze video content when transcription is not available
    Uses visual features to generate title, description, and tags
    """
    try:
        # Extract visual features
        features = extract_video_features(video_path, sample_frames=8)
        
        if "error" in features:
            raise ValueError(features["error"])
        
        # Generate analysis prompt based on features
        characteristics_str = ", ".join(features.get("characteristics", []))
        
        prompt = f"""
You are analyzing a video based on its visual characteristics (no audio transcription available).

VIDEO CHARACTERISTICS:
- Duration: {features['duration_seconds']} seconds
- Brightness Level: {features['avg_brightness']}/255
- Brightness Consistency: {features['brightness_consistency']} (lower = more consistent)
- Motion Level: {features['avg_motion']} (0-50 scale)
- Visual Features: {characteristics_str}

TASKS:
1. Generate a concise TITLE (max 12 words) describing what the video appears to show
2. Generate a BRIEF DESCRIPTION (2–3 sentences) based on visual analysis
3. Generate 6–10 TAGS suitable for video search

Rules:
- Use visual analysis to infer content (movement, lighting, composition)
- Tags should be lowercase
- Use single or two-word tags only
- Output must be in English

Return STRICT JSON ONLY:
{{
  "title": "string",
  "summary": "string",
  "tags": ["string"]
}}

Analyze and respond:
"""

        raw = ollama(prompt)
        
        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1

        if start == -1 or end == -1:
            raise RuntimeError(f"No JSON found in model output:\n{raw}")

        result = json.loads(raw[start:end])
        
        # Add visual analysis note to description
        if "summary" in result:
            result["summary"] = f"[Visual Analysis] {result['summary']}\n\n[Technical Details] Duration: {features['duration_seconds']}s, Brightness: {features['avg_brightness']}/255, Motion: {features['avg_motion']:.1f}"
        
        return result

    except Exception as e:
        print(f"Video content analysis error: {e}")
        # Return fallback result
        return {
            "title": "Video Analysis",
            "summary": f"Unable to analyze video content: {str(e)}",
            "tags": ["video", "unanalyzed"]
        }
