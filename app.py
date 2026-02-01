from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from models import db, VideoClip, TextDocument, Sequence, Takes
from dotenv import load_dotenv
import os, tempfile, json, io
from io import BytesIO

from utils.text.summarizer import summarize_text_file, summarize_pdf_file
from utils.media.transcription_summarizer import analyze_transcript, load_transcript
from utils.media.audio_transcription import transcribe_video
from utils.media.extract_thumbnail import extract_thumbnail
from utils.media.audio_conversion import mp4_to_mp3
from utils.media.video_analyzer import analyze_video_content
from utils.embedding_service import (
    add_or_update_video, add_or_update_document, delete_video, 
    delete_document, semantic_search, initialize_all_embeddings
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

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    # Handle search API requests (POST)
    if request.method == 'POST':
        data = request.get_json()
        query = data.get("query", "").strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        try:
            search_data = semantic_search(query, k=20)
            
            # Add timestamps and additional metadata to results
            results_with_timestamps = []
            for result in search_data['results']:
                if result['type'] == 'video':
                    clip = VideoClip.query.get(result['id'])
                    if clip:
                        result['timestamp'] = clip.timestamp.isoformat()
                        results_with_timestamps.append(result)
                else:  # document
                    doc = TextDocument.query.get(result['id'])
                    if doc:
                        result['timestamp'] = doc.timestamp.isoformat()
                        results_with_timestamps.append(result)
            
            return jsonify({
                "query": search_data["query"],
                "total": len(results_with_timestamps),
                "results": results_with_timestamps
            })
        except Exception as e:
            print(f"Search error: {e}")
            return jsonify({"error": f"Search failed: {str(e)}"}), 500
    
    # Handle initial page load (GET)
    video_clips = VideoClip.query.order_by(VideoClip.timestamp.desc()).all()
    text_docs = TextDocument.query.order_by(TextDocument.timestamp.desc()).all()
    
    all_items = video_clips + text_docs
    all_items.sort(key=lambda x: x.timestamp, reverse=True)
    
    return render_template('search.html', clips=all_items)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Normal direct upload workflow
    video = request.files.get("video")
    if not video:
        return jsonify({"error": "Video is required"}), 400

    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    # Read video file into memory
    video_data = video.read()
    filename = secure_filename(video.filename)

    # Create DB row with video data stored directly
    clip = VideoClip(
        title=title,
        description=description,
        tags=tags,
        video_data=video_data,
        video_filename=filename
    )

    db.session.add(clip)
    db.session.commit()

    # Generate thumbnail from video data
    try:
        # Create a temporary file to extract thumbnail
        tmp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        tmp_video.write(video_data)
        tmp_video.close()  # IMPORTANT: Close before FFmpeg reads it
        tmp_path = tmp_video.name
        
        thumbnail_data = extract_thumbnail(tmp_path, clip.id)
        if thumbnail_data:
            clip.thumbnail_data = thumbnail_data
            db.session.commit()
            print(f"✓ Thumbnail generated for clip {clip.id} ({len(thumbnail_data)} bytes)")
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
    except Exception as e:
        print(f"⚠ Error generating thumbnail: {e}")
        import traceback
        traceback.print_exc()
        # Create a placeholder thumbnail instead of failing
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (320, 180), color='#222222')
            draw = ImageDraw.Draw(img)
            draw.text((50, 70), "Video", fill='#666666')
            
            from io import BytesIO
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            clip.thumbnail_data = img_bytes.getvalue()
            db.session.commit()
            print(f"✓ Placeholder thumbnail created for clip {clip.id}")
        except Exception as e2:
            print(f"⚠ Could not create placeholder: {e2}")

    # Add to embedding database
    try:
        add_or_update_video(clip.id, title, description, tags)
    except Exception as e:
        print(f"Error adding to embeddings: {e}")

    return jsonify({
        "message": "Clip saved successfully",
        "clip_id": clip.id,
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

        try:
            # Try to analyze via transcription first
            mp3_path = mp4_to_mp3(video_path)
            transcript_path = transcribe_video(mp3_path)
            transcript = load_transcript(transcript_path)
            result = analyze_transcript(transcript)
            return jsonify(result)
        except Exception as e:
            print(f"Transcription analysis failed: {e}")
            print("Falling back to visual analysis...")
            
            try:
                # Fall back to visual analysis if transcription fails
                result = analyze_video_content(video_path)
                return jsonify(result)
            except Exception as e2:
                print(f"Visual analysis also failed: {e2}")
                return jsonify({
                    "error": f"Analysis failed. Transcription error: {str(e)}. Visual analysis error: {str(e2)}"
                }), 500

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

    # Read file data into memory
    file_data = file_obj.read()
    filename = secure_filename(file_obj.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    # Determine file type
    file_type = "pdf" if file_ext == ".pdf" else "text"

    # Create DB row with file data stored directly
    doc = TextDocument(
        title=title,
        description=description,
        tags=tags,
        document_data=file_data,
        document_filename=filename,
        file_type=file_type
    )

    db.session.add(doc)
    db.session.commit()

    # Add to embedding database
    try:
        add_or_update_document(doc.id, title, description, tags, file_type)
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
        # Delete from database (all data including thumbnail is removed)
        db.session.delete(clip)
        db.session.commit()

        # Delete from embeddings
        try:
            delete_video(clip_id)
        except Exception as e:
            print(f"Error deleting from embeddings: {e}")

        return jsonify({
            "message": "Clip deleted successfully",
            "redirect": "/search"
        })
    
    # Try to find as TextDocument
    doc = TextDocument.query.get(clip_id)
    
    if doc:
        # Delete from database (file data is automatically removed with the record)
        db.session.delete(doc)
        db.session.commit()

        # Delete from embeddings
        try:
            delete_document(clip_id)
        except Exception as e:
            print(f"Error deleting from embeddings: {e}")

        return jsonify({
            "message": "Document deleted successfully",
            "redirect": "/search"
        })
    
    return jsonify({"error": "Item not found"}), 404

@app.route("/edit/<int:clip_id>", methods=["GET"])
def edit_clip_page(clip_id):
    """Display edit page for a clip or document"""
    # Try video clip first
    clip = VideoClip.query.get(clip_id)
    if clip:
        return render_template('edit.html', clip=clip, item_type='video')
    
    # Try text document
    doc = TextDocument.query.get(clip_id)
    if doc:
        return render_template('edit.html', clip=doc, item_type='document')
    
    return "Item not found", 404

@app.route("/api/edit-clip/<int:clip_id>", methods=["POST"])
def edit_clip_api(clip_id):
    """Update clip or document metadata (title, description, tags)"""
    # Try video clip first
    clip = VideoClip.query.get(clip_id)
    if clip:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        tags = data.get('tags', '').strip()
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        try:
            clip.title = title
            clip.description = description
            clip.tags = tags
            db.session.commit()
            
            try:
                add_or_update_video(clip.id, title, description, tags)
            except Exception as e:
                print(f"Error updating embeddings: {e}")
            
            return jsonify({"message": "Clip updated successfully", "clip_id": clip.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update clip: {str(e)}"}), 500
    
    # Try text document
    doc = TextDocument.query.get(clip_id)
    if doc:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        tags = data.get('tags', '').strip()
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        try:
            doc.title = title
            doc.description = description
            doc.tags = tags
            db.session.commit()
            
            try:
                add_or_update_document(doc.id, title, description, tags, doc.file_type)
            except Exception as e:
                print(f"Error updating embeddings: {e}")
            
            return jsonify({"message": "Document updated successfully", "clip_id": doc.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update document: {str(e)}"}), 500
    
    return jsonify({"error": "Item not found"}), 404

@app.route("/video/<int:clip_id>")
def serve_video(clip_id):
    """Serve video file from database"""
    clip = VideoClip.query.get(clip_id)
    
    if not clip or not clip.video_data:
        return "Video not found", 404
    
    return send_file(
        BytesIO(clip.video_data),
        mimetype='video/mp4',
        as_attachment=False,
        download_name=clip.video_filename
    )

@app.route("/document/<int:doc_id>")
def serve_document(doc_id):
    """Serve document file from database"""
    doc = TextDocument.query.get(doc_id)
    
    if not doc or not doc.document_data:
        return "Document not found", 404
    
    # Determine MIME type based on file type
    if doc.file_type == 'pdf':
        mimetype = 'application/pdf'
    else:
        mimetype = 'text/plain'
    
    return send_file(
        BytesIO(doc.document_data),
        mimetype=mimetype,
        as_attachment=False,
        download_name=doc.document_filename
    )

@app.route("/thumbnail/<int:clip_id>")
def serve_thumbnail(clip_id):
    """Serve thumbnail image from database"""
    clip = VideoClip.query.get(clip_id)
    
    if not clip or not clip.thumbnail_data:
        return "Thumbnail not found", 404
    
    return send_file(
        BytesIO(clip.thumbnail_data),
        mimetype='image/jpeg',
        as_attachment=False,
        download_name=f'thumbnail_{clip_id}.jpg'
    )

@app.route("/sequences", methods=['GET'], endpoint='view_sequences')
def view_sequences():
    """View all saved sequences"""
    sequences = Sequence.query.order_by(Sequence.timestamp.desc()).all()
    return render_template('sequences.html', sequences=sequences)

@app.route("/scenes", methods=['GET'], endpoint='view_scenes')
def view_scenes():
    """View all scenes with their takes"""
    return render_template('scenes.html')

@app.route("/api/sequence/save", methods=['POST'])
def save_sequence():
    """Save a new sequence"""
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    clips = data.get('clips', [])
    
    if not name:
        return jsonify({"error": "Sequence name is required"}), 400
    
    if not clips or len(clips) == 0:
        return jsonify({"error": "At least one clip is required"}), 400
    
    try:
        # Extract just the IDs from clip objects
        clip_ids = [str(clip['id']) if isinstance(clip, dict) else str(clip) for clip in clips]
        
        sequence = Sequence(
            name=name,
            description=description
        )
        sequence.set_clips(clip_ids)
        
        db.session.add(sequence)
        db.session.commit()
        
        return jsonify({
            "message": "Sequence saved successfully",
            "id": sequence.id,
            "redirect": "/sequences"
        }), 201
    except Exception as e:
        print(f"Error saving sequence: {e}")
        return jsonify({"error": f"Failed to save sequence: {str(e)}"}), 500

@app.route("/api/sequence/<int:sequence_id>", methods=['GET'])
def get_sequence(sequence_id):
    """Get a specific sequence with its clips"""
    sequence = Sequence.query.get(sequence_id)
    
    if not sequence:
        return jsonify({"error": "Sequence not found"}), 404
    
    try:
        clip_ids = sequence.get_clips()
        clips_data = []
        
        for clip_id in clip_ids:
            # Try to find as VideoClip
            clip = VideoClip.query.get(int(clip_id))
            if clip:
                clips_data.append({
                    'id': clip.id,
                    'title': clip.title,
                    'description': clip.description,
                    'tags': clip.tags,
                    'type': 'video',
                    'timestamp': clip.timestamp.isoformat()
                })
            else:
                # Try to find as TextDocument
                doc = TextDocument.query.get(int(clip_id))
                if doc:
                    clips_data.append({
                        'id': doc.id,
                        'title': doc.title,
                        'description': doc.description,
                        'tags': doc.tags,
                        'type': 'document',
                        'file_type': doc.file_type,
                        'timestamp': doc.timestamp.isoformat()
                    })
        
        return jsonify({
            'id': sequence.id,
            'name': sequence.name,
            'description': sequence.description,
            'clip_count': sequence.clip_count,
            'timestamp': sequence.timestamp.isoformat(),
            'clips': clips_data
        })
    except Exception as e:
        print(f"Error fetching sequence: {e}")
        return jsonify({"error": f"Failed to fetch sequence: {str(e)}"}), 500

@app.route("/api/sequence/<int:sequence_id>", methods=['DELETE'])
def delete_sequence(sequence_id):
    """Delete a sequence"""
    sequence = Sequence.query.get(sequence_id)
    
    if not sequence:
        return jsonify({"error": "Sequence not found"}), 404
    
    try:
        db.session.delete(sequence)
        db.session.commit()
        
        return jsonify({
            "message": "Sequence deleted successfully",
            "redirect": "/sequences"
        })
    except Exception as e:
        print(f"Error deleting sequence: {e}")
        return jsonify({"error": f"Failed to delete sequence: {str(e)}"}), 500

@app.route('/upload-type')
def upload_type():
    return render_template('upload-type.html')

@app.route('/upload-take', methods=['GET', 'POST'])
def upload_take():
    from models import Takes, VideoClip
    from utils.media.extract_thumbnail import extract_thumbnail
    import tempfile
    import os
    
    if request.method == 'GET':
        return render_template('upload-take.html')
    # POST: handle take upload
    video = request.files.get('video')
    clip_id = request.form.get('clip_id')
    if not video or not clip_id:
        return jsonify({'error': 'Video and clip_id required'}), 400
    try:
        clip_id = int(clip_id)
    except Exception:
        return jsonify({'error': 'Invalid clip_id'}), 400
    original = VideoClip.query.get(clip_id)
    if not original:
        return jsonify({'error': 'Original clip not found'}), 404
    
    # Read video data into memory
    video_data = video.read()
    filename = secure_filename(video.filename)
    
    # Save to temp file to generate thumbnail
    thumbnail_data = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(video_data)
            tmp_path = tmp.name
        
        # Generate thumbnail
        thumbnail_data = extract_thumbnail(tmp_path, clip_id)
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        thumbnail_data = None
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    take_clip = VideoClip(
        title=original.title,
        description=original.description,
        tags=original.tags,
        video_data=video_data,
        video_filename=filename,
        thumbnail_data=thumbnail_data
    )
    db.session.add(take_clip)
    db.session.commit()
    
    # Group in Takes
    takes = Takes.query.filter_by(scene_name=original.title).first()
    if takes:
        ids = takes.get_clips()
        # Only add the new take, not the original clip again
        if take_clip.id not in ids:
            ids.append(take_clip.id)
        takes.set_clips(ids)
        db.session.commit()
    else:
        # Create new Takes entry with original clip and first take
        takes = Takes(scene_name=original.title, description=original.description)
        takes.set_clips([clip_id, take_clip.id])
        db.session.add(takes)
        try:
            db.session.commit()
        except Exception as e:
            # If unique constraint fails, try to get existing and update
            db.session.rollback()
            takes = Takes.query.filter_by(scene_name=original.title).first()
            if takes:
                ids = takes.get_clips()
                if take_clip.id not in ids:
                    ids.append(take_clip.id)
                takes.set_clips(ids)
                db.session.commit()
    return jsonify({'message': 'Take uploaded', 'redirect': '/takes'})

@app.route('/analyze-takes', methods=['POST'])
def analyze_takes_api():
    """
    Analyze takes using multimodal AI
    Optionally accepts criteria for content-based analysis
    """
    from models import Takes, VideoClip
    from utils.multimodal_analysis import analyze_takes, get_best_take_id
    
    data = request.get_json()
    scene_name = data.get('scene_name')
    criteria = data.get('criteria')  # Optional criteria like "surprised tone"
    
    if not scene_name:
        return jsonify({'error': 'scene_name required'}), 400
    
    takes_obj = Takes.query.filter_by(scene_name=scene_name).first()
    if not takes_obj:
        return jsonify({'error': 'Scene not found'}), 404
    
    clip_ids = takes_obj.get_clips()
    clips = [VideoClip.query.get(int(cid)) for cid in clip_ids if VideoClip.query.get(int(cid))]
    
    if not clips:
        return jsonify({'error': 'No clips found'}), 404
    
    try:
        scores, reasoning = analyze_takes(takes_obj, clips, criteria=criteria)
        best_id, best_reason = get_best_take_id(scores, reasoning, clips)
        
        return jsonify({
            'scores': scores,
            'reasoning': reasoning,
            'best_take_id': best_id,
            'best_reason': best_reason,
            'criteria_used': criteria
        })
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/select-best-take', methods=['POST'])
def select_best_take():
    """
    Manually select the best take for a scene
    """
    from models import Takes
    
    data = request.get_json()
    scene_name = data.get('scene_name')
    clip_id = data.get('clip_id')
    
    if not scene_name or not clip_id:
        return jsonify({'error': 'scene_name and clip_id required'}), 400
    
    takes_obj = Takes.query.filter_by(scene_name=scene_name).first()
    if not takes_obj:
        return jsonify({'error': 'Scene not found'}), 404
    
    try:
        takes_obj.best_take_id = int(clip_id)
        db.session.commit()
        return jsonify({'message': 'Best take selected', 'clip_id': clip_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/takes')
def view_takes():
    from models import Takes, VideoClip
    takes_list = Takes.query.order_by(Takes.timestamp.desc()).all()
    takes_data = []
    for take in takes_list:
        clip_ids = take.get_clips()
        clips = [VideoClip.query.get(int(cid)) for cid in clip_ids if VideoClip.query.get(int(cid))]
        takes_data.append({'scene_name': take.scene_name, 'description': take.description, 'clips': clips})
    return render_template('takes.html', takes=takes_data)


@app.route('/delete-takes/<scene_name>', methods=['POST'])
def delete_takes(scene_name):
    """
    Delete a takes group without deleting the underlying clips
    Only the Takes record is deleted, clips remain in database
    """
    from models import Takes
    
    takes_obj = Takes.query.filter_by(scene_name=scene_name).first()
    if not takes_obj:
        return jsonify({'error': 'Takes not found'}), 404
    
    try:
        db.session.delete(takes_obj)
        db.session.commit()
        
        return jsonify({
            'message': 'Takes deleted successfully. All clips have been preserved.',
            'redirect': '/takes'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting takes: {e}")
        return jsonify({'error': f'Failed to delete takes: {str(e)}'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize embeddings for all content on startup
        try:
            video_clips = VideoClip.query.all()
            text_documents = TextDocument.query.all()
            
            if video_clips or text_documents:
                initialize_all_embeddings(video_clips, text_documents)
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
    
    app.run()