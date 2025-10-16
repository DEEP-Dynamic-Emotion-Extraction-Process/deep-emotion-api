# app/models/__init__.py
from .user_model import User
from .video_model import Video, VideoStatus
from .frame_model import Frame # <-- ALTERAÇÃO AQUI
from .log_model import Log, LogLevel

# Opcional: você pode definir __all__ para controlar o que 'from .models import *' importa
__all__ = [
    'User',
    'Video',
    'VideoStatus',
    'Frame',
    # 'EmotionEnum', # <-- E AQUI
    'Log',
    'LogLevel',
]