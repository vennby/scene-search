import subprocess
import os

# Function to convert MP4 uploads to MP3 files, using ffmpeg

def mp4_to_mp3(mp4_path, mp3_path=None, bitrate="192k"):
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"ffmpeg not found at {ffmpeg_path}")

    mp4_path = os.path.abspath(mp4_path)

    if mp3_path is None:
        mp3_path = os.path.splitext(mp4_path)[0] + ".mp3"
    else:
        mp3_path = os.path.abspath(mp3_path)

    command = [
        ffmpeg_path,
        "-y",
        "-i", mp4_path,
        "-vn",
        "-map", "a",
        "-acodec", "libmp3lame",
        "-ab", bitrate,
        mp3_path
    ]

    subprocess.run(command, check=True)
    return mp3_path