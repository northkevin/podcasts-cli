from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_serializer

class PodcastHost(BaseModel):
    name: str
    title: Optional[str] = None
    role: str = "Host"

    @field_serializer('name', 'title', 'role')
    def serialize_str_fields(self, v: Optional[str], _info) -> Optional[str]:
        return v if v is not None else ""

class PodcastConfig(BaseModel):
    channel_id: str
    name: str
    host: PodcastHost
    default_tags: List[str] = []

    @field_serializer('default_tags')
    def serialize_tags(self, v: List[str], _info) -> List[str]:
        return v or [] 