import subprocess, os

# Function to generate transcription from video using Whisper CLI

def transcribe_video(video_path):
    cmd = [
    r"C:\whisper\whisper-cli.exe",
    "-m", r"C:\whisper\models\ggml-tiny.bin",
    "-f", video_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    transcript = result.stdout.strip()

    if not transcript:
        raise RuntimeError("Whisper produced no transcript")

    transcript_path = os.path.splitext(video_path)[0] + ".txt"

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)

    return transcript_path


