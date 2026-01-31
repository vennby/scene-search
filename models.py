from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class VideoClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(255))

    video_path = db.Column(db.String(512), nullable=False)
    thumbnail_path = db.Column(db.String(255), nullable=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    date_saved = db.Column(db.Date, default=lambda: datetime.utcnow().date())

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

    document_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'text' or 'pdf'

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    date_saved = db.Column(db.Date, default=lambda: datetime.utcnow().date())

    def __repr__(self):
        return f"<TextDocument {self.id}: {self.title}>"
