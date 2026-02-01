<h1 align="center"> scene-search </h1>

<p align="center"> A semantic search engine built for filmmakers and content creators who think in scenes.</p>

<img src="https://i.pinimg.com/originals/64/13/3f/64133f9d37e36786d3e91a70ea3e2dd3.gif" width="2000">

## What is scene-search?

Scene-search is a comprehensive video management system designed for post-production workflows. It combines semantic search, AI-powered video analysis, and intelligent metadata generation to help you organize, find, and manage video clips efficiently.

**Core capabilities:**
- Semantic search across video metadata and transcripts
- Automatic video analysis with metadata generation
- Shot sequencing and assembly editing assistance
- Multi-take scene management with AI-powered best take selection
- Database storage with full-text search and relevance ranking



## How It Works

### The Pipeline

**1. Upload & Transcription**
- Videos are uploaded directly to the system
- Audio is extracted and transcribed using Whisper

**2. Metadata Generation**
- LLM (qwen2.5) analyzes transcript or video content
- Generates: title, description, summary, and tags

**3. Semantic Indexing**
- All metadata (title, description, tags, transcript) combined
- Converted to semantic embeddings using SentenceTransformer
- Embeddings stored in Chroma vector database
- Telugu queries are automatically transliterated for search

**4. Search & Ranking**
- User query → embedded using same model
- Compared against all stored embeddings via cosine similarity
- Results ranked by relevance score
  
**5. Video Analysis**
- If transcription fails → fallback to visual analysis
- Advanced video analysis evaluates:
  - **Visual characteristics:** brightness, motion, saturation, edge density, composition
  - **Cinematography:** contrast level, color grade, visual complexity, editing pace, hue diversity
  - **Director styles:** recognizes Michael Bay, Wes Anderson, Spielberg, Nolan patterns
- Extracted features cached for faster subsequent searches


## Features & Workflows

### Semantic Search

**Traditional search:** "Find clips tagged 'action'"
→ Only returns clips explicitly tagged 'action'

**Semantic search:** "Show me fast-paced dramatic scenes"
→ Returns clips matching the semantic meaning, even if tagged differently

**How it works:**
- Your query converted to semantic embedding
- Compared against all video embeddings
- Returns ranked results by relevance
- Works across transcripts, titles, descriptions, tags

### Takes Management

**Problem:** You have multiple recordings of the same scene. Which one is best?

**Solution:** Create a "Scene" with multiple "Takes" and let AI pick the best one.

**Workflow:**
1. Upload multiple video clips of the same scene
2. Group them into a "Take" (all clips representing same scene)
3. Specify criteria: e.g., "sci-fi themed", "Michael Bay style", "calm and serene"
4. System analyzes each clip and scores based on criteria
5. Returns best take with reasoning

**AI Analysis for Takes:**
Each video gets analyzed for 10+ cinematographic metrics and scored accordingly.

### Video Analysis Fallback

**If transcription fails:**
- System extracts visual features (brightness, motion, colors)
- Uses LLM to understand what video shows visually
- Generates title, description, tags based purely on visual content
- No audio needed


## Technical Architecture

### Database Schema

```sql
VideoClip:
  id, title, description, tags
  video_data (BLOB), thumbnail_data (BLOB)
  timestamp, file_type

TextDocument:
  id, title, description, tags
  document_data (BLOB), file_type, timestamp

Takes:
  id, scene_name (unique), description
  clip_ids (JSON array), timestamp

Sequence:
  id, name, description
  clip_ids (JSON array), timestamp
```

Videos and thumbnails stored directly in database as BLOBs (binary data) for atomicity and easier deployment.

### Utils Modules

**embedding_service.py**
- Semantic embedding generation using SentenceTransformer
- Vector search against Chroma database
- Handles add, update, delete operations
- Returns ranked results with scores

**media/audio_transcription.py**
- Whisper-based transcription
- Standard English/common language support

**media/telugu_transcription.py** ← NEW
- Language detection (Telugu, Hindi, English)
- Telugu-specific transcription
- Telugu → English translation using LLM
- Mixed language handling
- Returns: (transcript, language_code, translation)

**media/video_analyzer.py**
- Visual analysis when transcription fails
- Feature extraction (brightness, motion, color)
- LLM-based content understanding
- Fallback metadata generation

**media/extract_thumbnail.py**
- Frame extraction from video
- Thumbnail generation and storage

**media/audio_conversion.py**
- MP4 → MP3 conversion for transcription

**text/summarizer.py**
- Text and PDF document summarization
- Metadata extraction for documents

**transliteration.py** ← NEW
- Telugu ↔ English character mapping
- Script detection (Telugu/Hindi/English)
- Query transliteration for search

**multimodal_analysis.py** ← UPGRADED
- Advanced cinematographic analysis
- 10+ visual metrics extraction
- Director style recognition
- Scene evaluation for takes selection

---

## Project Structure

```
scene-search/
├── app.py                          # Flask routes and main logic
├── models.py                       # SQLAlchemy models
├── requirements.txt                # Python dependencies
├── chroma_db/                      # Vector database
├── instance/                       # Flask instance folder
├── uploads/                        # Uploaded files (if used)
│
├── templates/
│   ├── index.html                  # Home page
│   ├── choice.html                 # Upload type selection
│   ├── upload.html                 # Video upload & analysis
│   ├── search.html                 # Search interface
│   ├── create.html                 # Sequence creation
│   ├── sequences.html              # Sequence management
│   ├── takes.html                  # Takes management & analysis
│   ├── text.html                   # Text document upload
│   └── edit.html                   # Clip editing
│
├── static/
│   ├── css/
│   │   ├── common.css              # Shared styles
│   │   ├── search.css              # Search page styles
│   │   ├── sequences.css           # Sequences page styles
│   │   ├── takes.css               # Takes page styles
│   │   └── create.css              # Create page styles
│   │
│   └── js/
│       ├── dropdown.js             # Navigation dropdown
│       ├── search.js               # Search logic & Telugu support
│       ├── sequences.js            # Sequence management
│       ├── takes.js                # Takes management & analysis
│       └── create.js               # Sequence creation
│
└── utils/
    ├── embedding_service.py        # Semantic search
    ├── transliteration.py          # Telugu transliteration
    ├── multimodal_analysis.py      # Advanced video analysis
    │
    ├── media/
    │   ├── audio_transcription.py  # Whisper transcription
    │   ├── telugu_transcription.py # Telugu support
    │   ├── video_analyzer.py       # Visual analysis fallback
    │   ├── extract_thumbnail.py    # Thumbnail extraction
    │   ├── audio_conversion.py     # MP4 → MP3
    │   └── transcription_summarizer.py # Metadata generation
    │
    └── text/
        └── summarizer.py           # Text/PDF summarization
```

## How to Run

### Prerequisites
- Python 3.8+
- FFmpeg (for video processing)
- Whisper CLI (for transcription)
- Ollama running locally (for LLM analysis)

### Setup

1. Clone and navigate:
```bash
cd scene-search
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start Ollama service:
```bash
ollama serve
# In another terminal, pull model:
ollama pull qwen2.5
```

5. Run Flask:
```bash
python app.py
```

6. Open browser:
```
http://localhost:5000
```

---

## Known Limitations & Future Improvements

**Current:**
- Telugu transcription is still in development
- Large videos take time to analyze (could fine-tune models or upgrade to paid ones)
- Composition analysis basic (could improve with ML models)

**Potential:**
- Multi-language support (add Hindi, Tamil, Kannada)
- Advanced object detection in videos
- Batch analysis for multiple videos
- Export workflows to NLE (Premiere, DaVinci Resolve)


## Configuration

Key settings in `app.py`:
```python
UPLOAD_FOLDER = "uploads"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5"
TEMPERATURE = 0.3
```

Chroma vector database configured in `embedding_service.py`:
```python
client = chromadb.Client()
collection = client.get_or_create_collection(
    name="scene_search",
    metadata={"hnsw:space": "cosine"}
)
```

## License & Credits

Built with 💖 by [venn](https://linkedin.com/in/venn-v)!