import os, subprocess

def extract_thumbnail(video_path, clip_id):
    thumb_dir = "static/thumbnails"
    os.makedirs(thumb_dir, exist_ok=True)

    out = f"{thumb_dir}/clip_{clip_id}.jpg"

    subprocess.run([
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "-y",
        "-i", video_path,
        "-ss", "00:00:02",
        "-vframes", "1",
        out
    ], check=True)

    return f"thumbnails/clip_{clip_id}.jpg"
