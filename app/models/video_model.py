# app/models/video_model.py
import uuid
import enum
from datetime import datetime
from app.extensions import db

# Usar Enums do Python torna o código mais legível e seguro
class VideoStatus(enum.Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class Video(db.Model):
    __tablename__ = 'videos'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.Enum(VideoStatus, native_enum=False), nullable=False, default=VideoStatus.PENDING)
    frame_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Float, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relacionamentos
    user = db.relationship('User', back_populates='videos')
    frames = db.relationship('Frame', back_populates='video', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Video {self.id} - {self.title}>'