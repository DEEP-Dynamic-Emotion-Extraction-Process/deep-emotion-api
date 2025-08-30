# app/models/frame_model.py
import enum
from app.extensions import db

class EmotionEnum(enum.Enum):
    HAPPY = 'HAPPY'
    SAD = 'SAD'
    ANGRY = 'ANGRY'
    SURPRISED = 'SURPRISED'
    NEUTRAL = 'NEUTRAL'
    FEAR = 'FEAR'
    DISGUST = 'DISGUST'

class Frame(db.Model):
    __tablename__ = 'frames'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(36), db.ForeignKey('videos.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    video_timestamp_sec = db.Column(db.Float, nullable=False)
    emotion = db.Column(db.Enum(EmotionEnum), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    # Relacionamento
    video = db.relationship('Video', back_populates='frames')

    # Garante que a combinação de video_id e frame_number seja única
    __table_args__ = (db.UniqueConstraint('video_id', 'frame_number', name='uq_video_frame'),)

    def __repr__(self):
        return f'<Frame {self.id} for Video {self.video_id}>'