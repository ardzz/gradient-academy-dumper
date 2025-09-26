"""Pydantic models for API responses."""
from typing import List, Optional

from pydantic import BaseModel


class Course(BaseModel):
    """Course model from API."""
    id: str
    course_name: str
    slug: str
    cover: Optional[str] = None
    thumbnail: Optional[str] = None
    trailer: Optional[str] = None
    is_free: Optional[bool] = None
    is_coming_soon: Optional[bool] = False
    is_new: Optional[bool] = None


class Chapter(BaseModel):
    """Chapter model from API."""
    chapter_id: str
    chapter_name: str
    order: int
    subchapter_counts: int
    is_coming_soon: Optional[bool] = False


class Subchapter(BaseModel):
    """Subchapter model from API."""
    id: str
    type: str  # video, exercise, etc.
    order: int
    subchapter_name: str
    subchapter_slug: str
    duration: Optional[str] = None
    is_free: Optional[bool] = None
    thumbnail: Optional[str] = None
    video_id: Optional[str] = None
    exercise_id: Optional[str] = None


class Lecturer(BaseModel):
    """Lecturer model from API."""
    id: str
    name: str
    role: Optional[str] = None
    photo: Optional[str] = None


class Video(BaseModel):
    """Video model from API."""
    id: str
    video_url: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    is_free: Optional[bool] = None
    drm_video_url: Optional[str] = None
    is_drm_protected: Optional[bool] = None
    token: Optional[str] = None
    drm_token: Optional[str] = None
    mux_playback_id: Optional[str] = None
    lecturers: Optional[List[Lecturer]] = None


class SubchapterDetail(BaseModel):
    """Detailed subchapter model from API."""
    id: str
    subchapter_name: str
    subchapter_slug: str
    type_name: str
    thumbnail: Optional[str] = None
    order: int
    video: Optional[Video] = None
    chapter_id: str
    chapter_name: str