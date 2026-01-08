from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class VideoClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    date_saved = db.Column(db.Date, default=datetime.utcnow().date)

    def __repr__(self):
        return f'<VideoClip {self.title}>'
