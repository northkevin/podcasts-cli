from typing import List, Optional
from pydantic import BaseModel

class PodcastHost(BaseModel):
    name: str
    title: Optional[str] = None
    role: str = "Host"

class PodcastConfig(BaseModel):
    channel_id: str
    name: str
    host: PodcastHost
    default_tags: List[str] = [] 