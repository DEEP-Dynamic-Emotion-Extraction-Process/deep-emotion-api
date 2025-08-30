# app/models/user_model.py
import uuid
from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos:
    # 'cascade' garante que os vídeos e logs de um usuário sejam deletados se o usuário for deletado.
    # 'lazy='dynamic'' retorna um objeto de query, útil para coleções grandes.
    videos = db.relationship('Video', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
    logs = db.relationship('Log', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        """Cria o hash da senha."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'