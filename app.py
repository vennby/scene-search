from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from models import db, VideoClip, TextDocument
from dotenv import load_dotenv
import os, tempfile

from utils.text.summarizer import summarize_text_file, summarize_pdf_file
from utils.media.transcription_summarizer import analyze_transcript, load_transcript
from utils.media.audio_transcription import transcribe_video
from utils.media.extract_thumbnail import extract_thumbnail
from utils.media.audio_conversion import mp4_to_mp3
from utils.embedding_service import (
    add_video_clip, add_text_document, delete_video_clip, 
    delete_text_document, semantic_search, initialize_embeddings
)

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

@app.route('/choice')
def choice():
    return render_template('choice.html')

@app.route('/text', endpoint='text')
def text_upload():
    return render_template('text.html')

@app.route('/search')
def search():
    # Get all video clips
    video_clips = VideoClip.query.order_by(VideoClip.timestamp.desc()).all()
    
    # Get all text documents and add file_type attribute for compatibility
    text_docs = TextDocument.query.order_by(TextDocument.timestamp.desc()).all()
    for doc in text_docs:
        doc.file_type = doc.file_type  # Already stored in DB
    
    # Combine and sort by timestamp
    all_items = video_clips + text_docs
    all_items.sort(key=lambda x: x.timestamp, reverse=True)
    
    return render_template('search.html', clips=all_items)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    video = request.files.get("video")
    if not video:
        return jsonify({"error": "Video is required"}), 400

    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    # Save video
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(video_path)

    # Create DB row WITH video_path
    clip = VideoClip(
        title=title,
        description=description,
        tags=tags,
        video_path=video_path
    )

    db.session.add(clip)
    db.session.commit()

    # Generate thumbnail AFTER we have clip.id
    thumbnail_path = extract_thumbnail(video_path, clip.id)
    clip.thumbnail_path = thumbnail_path
    db.session.commit()

    # Add to embedding database
    try:
        add_video_clip(clip.id, title, description, tags)
    except Exception as e:
        print(f"Error adding to embeddings: {e}")

    return jsonify({
        "message": "Clip saved successfully",
        "redirect": "/search"
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    video = request.files.get("video")
    if not video:
        return jsonify({"error": "No video uploaded"}), 400

    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, video.filename)
        video.save(video_path)

        mp3_path = mp4_to_mp3(video_path)
        transcript_path = transcribe_video(mp3_path)
        transcript = load_transcript(transcript_path)

        result = analyze_transcript(transcript)

        return jsonify(result)

@app.route("/text/analyze", methods=["POST"])
def analyze_text():
    file_obj = request.files.get("file")
    if not file_obj:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file_obj.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, filename)
        file_obj.save(file_path)

        try:
            # Handle PDF files
            if file_ext == ".pdf":
                result = summarize_pdf_file(file_path)
            # Handle text files
            elif file_ext == ".txt":
                result = summarize_text_file(file_path)
            else:
                return jsonify({"error": f"Unsupported file type: {file_ext}. Please upload .txt or .pdf files"}), 400

            return jsonify(result)
        except Exception as e:
            print(f"Analysis error: {e}")
            return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/text/upload", methods=["POST"])
def upload_text():
    file_obj = request.files.get("file")
    if not file_obj:
        return jsonify({"error": "File is required"}), 400

    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    # Save file
    filename = secure_filename(file_obj.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file_obj.save(file_path)

    # Determine file type
    file_type = "pdf" if file_ext == ".pdf" else "text"

    # Create DB row using TextDocument
    doc = TextDocument(
        title=title,
        description=description,
        tags=tags,
        document_path=file_path,
        file_type=file_type
    )

    db.session.add(doc)
    db.session.commit()

    # Add to embedding database
    try:
        add_text_document(doc.id, title, description, tags, file_type)
    except Exception as e:
        print(f"Error adding to embeddings: {e}")

    return jsonify({
        "message": "Document saved successfully",
        "redirect": "/search"
    })

@app.route("/delete/<int:clip_id>", methods=["POST"])
def delete_clip(clip_id):
    # Try to find as VideoClip first
    clip = VideoClip.query.get(clip_id)
    
    if clip:
        try:
            # Delete file from disk if it exists
            if os.path.exists(clip.video_path):
                os.remove(clip.video_path)
            
            # Delete thumbnail if it exists
            if clip.thumbnail_path and os.path.exists(clip.thumbnail_path):
                os.remove(clip.thumbnail_path)
        except Exception as e:
            print(f"Error deleting files: {e}")

        # Delete from database
        db.session.delete(clip)
        db.session.commit()

        # Delete from embeddings
        try:
            delete_video_clip(clip_id)
        except Exception as e:
            print(f"Error deleting from embeddings: {e}")

        return jsonify({
            "message": "Clip deleted successfully",
            "redirect": "/search"
        })
    
    # Try to find as TextDocument
    doc = TextDocument.query.get(clip_id)
    
    if doc:
        try:
            # Delete file from disk if it exists
            if os.path.exists(doc.document_path):
                os.remove(doc.document_path)
        except Exception as e:
            print(f"Error deleting files: {e}")

        # Delete from database
        db.session.delete(doc)
        db.session.commit()

        # Delete from embeddings
        try:
            delete_text_document(clip_id)
        except Exception as e:
            print(f"Error deleting from embeddings: {e}")

        return jsonify({
            "message": "Document deleted successfully",
            "redirect": "/search"
        })
    
    return jsonify({"error": "Item not found"}), 404

@app.route("/api/search", methods=["POST"])
def api_search():
    """Semantic search API endpoint"""
    data = request.get_json()
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        # Perform semantic search
        search_results = semantic_search(query, k=20)
        
        # Fetch full objects from database
        results_with_data = []
        
        for result in search_results:
            if result["type"] == "video":
                clip = VideoClip.query.get(result["id"])
                if clip:
                    results_with_data.append({
                        "id": clip.id,
                        "title": clip.title,
                        "description": clip.description,
                        "tags": clip.tags,
                        "file_type": "video",
                        "timestamp": clip.timestamp.isoformat(),
                        "score": result["score"]
                    })
            else:  # text or pdf
                doc = TextDocument.query.get(result["id"])
                if doc:
                    results_with_data.append({
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description,
                        "tags": doc.tags,
                        "file_type": doc.file_type,
                        "timestamp": doc.timestamp.isoformat(),
                        "score": result["score"]
                    })
        
        return jsonify({
            "query": query,
            "count": len(results_with_data),
            "results": results_with_data
        })
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize embeddings on startup
        try:
            video_clips = VideoClip.query.all()
            text_documents = TextDocument.query.all()
            
            if video_clips or text_documents:
                initialize_embeddings(video_clips, text_documents)
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
    
    app.run()