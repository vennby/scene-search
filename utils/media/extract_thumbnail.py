import os, subprocess, tempfile

def extract_thumbnail(video_path, clip_id):
    """Extract thumbnail from video and return as binary data"""
    tmp_jpg = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    tmp_jpg.close()  # Close file so FFmpeg can write to it
    tmp_path = tmp_jpg.name

    try:
        result = subprocess.run([
            r"C:\ffmpeg\bin\ffmpeg.exe",
            "-y",
            "-i", video_path,
            "-ss", "00:00:02",
            "-vframes", "1",
            tmp_path
        ], capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg failed: {result.stderr}")

        # Read thumbnail file as binary
        if not os.path.exists(tmp_path):
            raise Exception(f"Thumbnail file not created at {tmp_path}")
        
        with open(tmp_path, 'rb') as f:
            thumbnail_data = f.read()
        
        if not thumbnail_data:
            raise Exception("Thumbnail data is empty")
        
        return thumbnail_data
    
    except Exception as e:
        print(f"Thumbnail extraction error: {e}")
        raise
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass
