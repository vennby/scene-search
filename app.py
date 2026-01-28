from flask import Flask, render_template, request, jsonify
from models import db, VideoClip
from dotenv import load_dotenv
import os, tempfile

from utils.transcription_summarizer import analyze_transcript, load_transcript
from utils.audio_transcription import transcribe_video
from utils.audio_conversion import mp4_to_mp3

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scene_search.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    clips = VideoClip.query.order_by(VideoClip.timestamp.desc()).all()
    return render_template('search.html', clips=clips)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags')
        # Optionally handle file upload here
        clip = VideoClip(title=title, description=description, tags=tags)
        db.session.add(clip)
        db.session.commit()
        return jsonify({'message': 'Clip saved successfully!', 'redirect': '/search'})
    return render_template('upload.html')

@app.route("/analyze", methods=["POST"])
def analyze():
    video = request.files["video"]

    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, video.filename)
        txt_path = video_path + ".txt"

        video.save(video_path)

        result = analyze_transcript(load_transcript(transcribe_video(mp4_to_mp3(video_path))))
        
        # Ensure result has proper structure with title, description, and tags
        if isinstance(result, dict):
            result.setdefault('title', 'Untitled Clip')
            result.setdefault('description', result.get('summary', ''))
            result.setdefault('tags', '')

        return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()