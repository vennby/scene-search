from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from datetime import timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

db = SQLAlchemy()

class VideoClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(255))

    # Store video file data directly in database
    video_data = db.Column(db.LargeBinary, nullable=False)
    video_filename = db.Column(db.String(255), nullable=False)
    
    # Store thumbnail data directly in database
    thumbnail_data = db.Column(db.LargeBinary, nullable=True)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    date_saved = db.Column(db.Date, default=lambda: datetime.now(IST).date())

    @property
    def file_type(self):
        return "video"

    def __repr__(self):
        return f"<VideoClip {self.id}: {self.title}>"
    
class TextDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(255))

    # Store document file data directly in database
    document_data = db.Column(db.LargeBinary, nullable=False)
    document_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'text' or 'pdf'

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    date_saved = db.Column(db.Date, default=lambda: datetime.now(IST).date())

    def __repr__(self):
        return f"<TextDocument {self.id}: {self.title}>"

class Sequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Store clip IDs and order as JSON
    clip_ids = db.Column(db.Text, nullable=False)  # JSON string of clip IDs in order
    clip_count = db.Column(db.Integer, default=0)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    def get_clips(self):
        """Parse clip_ids JSON and return list of IDs"""
        try:
            return json.loads(self.clip_ids)
        except:
            return []
    
    def set_clips(self, clip_list):
        """Store clip list as JSON"""
        self.clip_ids = json.dumps(clip_list)
        self.clip_count = len(clip_list)
    
    def __repr__(self):
        return f"<Sequence {self.id}: {self.name}>"

class Takes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Represents the scene these takes belong to
    scene_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)

    # Store different takes of the same scene
    # JSON list of clip IDs (order is optional, but preserved if provided)
    clip_ids = db.Column(db.Text, nullable=False)
    take_count = db.Column(db.Integer, default=0)

    timestamp = db.Column(db.DateTime, default=datetime.now(IST))

    def get_clips(self):
        """Return list of clip IDs for this scene's takes"""
        try:
            return json.loads(self.clip_ids)
        except Exception:
            return []

    def set_clips(self, clip_list):
        """Store take clip IDs as JSON"""
        self.clip_ids = json.dumps(clip_list)
        self.take_count = len(clip_list)

    def __repr__(self):
        return f"<Takes {self.id}: Scene='{self.scene_name}', Takes={self.take_count}>"
