import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from ...config import Config
from ..generators.id import IDGenerator
from .schemas import PodcastEntry, Metadata, Interviewee

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class PodcastEntry(BaseModel):
    episode_id: str
    url: str
    platform: str
    title: str
    description: str
    published_at: datetime
    podcast_name: str
    interviewee: Interviewee
    webvtt_url: str
    status: str = "pending"
    episodes_file: str = ""
    transcripts_file: str = ""
    
    @property
    def process_command(self) -> str:
        return f"python -m podcasts process-podcast --episode_id {self.episode_id}"
    
    @classmethod
    def from_metadata(cls, metadata: Metadata, platform: str, episode_id: str) -> "PodcastEntry":
        """Create entry from metadata"""
        return cls(
            episode_id=episode_id,
            url=str(metadata.url),
            platform=platform,
            title=metadata.title,
            description=metadata.description,
            published_at=metadata.published_at,
            podcast_name=metadata.podcast_name,
            interviewee=metadata.interviewee,
            webvtt_url=metadata.webvtt_url
        )

class PodcastList:
    def __init__(self):
        self.entries: List[PodcastEntry] = []
        self._load()
    
    def _load(self):
        """Load podcast list from file"""
        try:
            if Config.PODCAST_LIST.exists():
                with open(Config.PODCAST_LIST, 'r') as f:
                    data = json.load(f)
                    self.entries = [PodcastEntry.parse_obj(entry) for entry in data]
                    
        except Exception as e:
            logger.error(f"Failed to load podcast list: {e}")
            self.entries = []
    
    def _save(self):
        """Save podcast list to file"""
        try:
            data = [entry.dict() for entry in self.entries]
            with open(Config.PODCAST_LIST, 'w') as f:
                json.dump(data, f, indent=2, cls=DateTimeEncoder)
                
        except Exception as e:
            logger.error(f"Failed to save podcast list: {e}")
    
    def add_entry(self, url: str, platform: str, metadata: Metadata, existing_id: Optional[str] = None) -> PodcastEntry:
        """Add new podcast entry"""
        # Generate or reuse episode ID
        episode_id = existing_id or IDGenerator().generate_id(
            platform=platform,
            published_at=metadata.published_at,
            interviewee_name=metadata.interviewee.name
        )
        
        # Create entry from metadata
        entry = PodcastEntry.from_metadata(metadata, platform, episode_id)
        
        self.entries.append(entry)
        self._save()
        
        return entry
    
    def get_entry(self, episode_id: str) -> Optional[PodcastEntry]:
        """Get podcast entry by ID"""
        return next(
            (entry for entry in self.entries if entry.episode_id == episode_id),
            None
        )
    
    def update_entry(self, episode_id: str, **kwargs):
        """Update podcast entry"""
        entry = self.get_entry(episode_id)
        if entry:
            # Update fields and validate with Pydantic
            updated_data = entry.dict()
            updated_data.update(kwargs)
            self.entries[self.entries.index(entry)] = PodcastEntry.parse_obj(updated_data)
            self._save()

def save_state(episode_id: str, status: str = "processing", error: Optional[str] = None):
    """Save podcast processing state"""
    podcast_list = PodcastList()
    entry = podcast_list.get_entry(episode_id)
    
    if entry:
        entry.status = status
        podcast_list._save()
        
        if error:
            logger.error(f"Error processing {episode_id}: {error}")