# app/models/log_model.py
import enum
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.mysql import JSON # Para MySQL. Para outros bancos, use db.JSON

class LogLevel(enum.Enum):
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento
    user = db.relationship('User', back_populates='logs')

    def __repr__(self):
        return f'<Log {self.id} - {self.action}>'