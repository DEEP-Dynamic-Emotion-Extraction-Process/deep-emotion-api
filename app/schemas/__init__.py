# app/schemas/__init__.py
from .user_schema import UserSchema, UserRegistrationSchema
from .video_schema import VideoSchema, VideoDetailSchema, VideoUpdateSchema
from .frame_schema import FrameSchema
from .log_schema import LogSchema

__all__ = [
    "UserSchema",
    "UserRegistrationSchema",
    "VideoSchema",
    "VideoDetailSchema",
    "VideoUpdateSchema",
    "FrameSchema",
    "LogSchema",
]