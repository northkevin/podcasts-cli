from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_serializer

class Speaker(BaseModel):
    name: str
    title: Optional[str] = None
    role: str = "Guest"
    profession: Optional[str] = None
    organization: Optional[str] = None

    @field_serializer('name', 'title', 'role', 'profession', 'organization')
    def serialize_str_fields(self, v: Optional[str], _info) -> Optional[str]:
        return v if v is not None else ""

class YouTubeMetadata(BaseModel):
    channel_id: str
    channel_title: str
    channel_url: str
    video_id: str
    episode_number: Optional[str] = None
    playlist_id: Optional[str] = None
    playlist_title: Optional[str] = None
    category_id: str
    tags: List[str] = []
    default_language: Optional[str] = None
    thumbnail_url: Optional[str] = None

    @field_serializer('tags')
    def serialize_tags(self, v: List[str], _info) -> List[str]:
        return v or [] 