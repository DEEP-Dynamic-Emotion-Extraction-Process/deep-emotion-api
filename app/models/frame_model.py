# app/models/frame_model.py
from app.extensions import db
from sqlalchemy.dialects.mysql import JSON # Importe o tipo JSON

class Frame(db.Model):
    __tablename__ = 'frames'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(36), db.ForeignKey('videos.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    video_timestamp_sec = db.Column(db.Float, nullable=False)
    
    # Coluna JSON para armazenar todas as emoções e confianças
    emotions = db.Column(JSON, nullable=True)

    # Relacionamento (usa uma string 'Video' para evitar importações circulares)
    video = db.relationship('Video', back_populates='frames')

    # Garante que a combinação de video_id e frame_number seja única
    __table_args__ = (db.UniqueConstraint('video_id', 'frame_number', name='uq_video_frame'),)

    def __repr__(self):
        return f'<Frame {self.id} for Video {self.video_id}>'