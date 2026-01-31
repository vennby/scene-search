<h1 align="center"> scene-search </h1>

<p align="center"> A semantic search engine built for filmmakers and content creators who think in scenes.</p>

<img src="https://i.pinimg.com/originals/64/13/3f/64133f9d37e36786d3e91a70ea3e2dd3.gif" width="2000">

### TLDR; What is **scene-search**?
- Bilingual search engine for post-production footage.
- Indexes footage using transcripts, supports natural language queries, returns clips with timestamps and relevance ranking.

### Problems yet to fix
- Chunking and summarizing the chunks is too slow

### How does scene-search work?
1. **Upload**: Videos/documents are stored with title, description, and tags
2. **Embed**: Metadata is combined and converted to semantic embeddings using SentenceTransformer
3. **Index**: Embeddings stored in Chroma vector DB with metadata
4. **Search**: Query is embedded using same model and compared via cosine similarity
5. **Rank**: Results sorted by similarity score and returned to user

`utils` has the following modules:
- `embedding_service.py` - Semantic embeddings and vector search (Chroma DB)
- `media/audio_transcription.py` - Audio transcription from videos
- `media/extract_thumbnail.py` - Thumbnail extraction from videos
- `media/audio_conversion.py` - MP4 to MP3 conversion
- `text/summarizer.py` - Text and PDF summarization

<h3> How to Run? </h3>
1. Navigate to the project root:
<pre>cd scene-search</pre>

2. Install dependencies:
<pre>pip install -r requirements.txt</pre>

3. Run the Flask app:
<pre>python app.py</pre>

4. Open your browser to `http://localhost:5000` and start uploading content!

### Project Structure
```
scene-search/
├── app.py                          # Flask application and routes
├── models.py                       # SQLAlchemy database models
├── chroma_db/                      # Vector database (auto-created)
├── uploads/                        # Uploaded files storage
├── utils/
│   ├── embedding_service.py        # Semantic search logic
│   ├── media/                      # Video processing utilities
│   └── text/                       # Text processing utilities
├── templates/                      # HTML pages
└── static/                         # CSS and JS assets
```

### Database Schema
- **VideoClip**: id, title, description, tags, video_path, thumbnail_path, timestamp
- **TextDocument**: id, title, description, tags, document_path, file_type (text/pdf), timestamp