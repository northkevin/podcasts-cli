import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

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
    duration_seconds: int
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
            webvtt_url=metadata.webvtt_url,
            duration_seconds=metadata.duration_seconds
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
                    self.entries = [PodcastEntry.model_validate(entry) for entry in data]
        except Exception as e:
            logger.warning(f"Failed to load podcast list: {e}")
    
    def _save(self):
        """Save podcast list to file"""
        try:
            with open(Config.PODCAST_LIST, 'w') as f:
                json_data = [entry.model_dump() for entry in self.entries]
                json.dump(json_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save podcast list: {e}")
            raise
    
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
        
        # Set file paths using Config methods
        entry.episodes_file = str(Config.get_episodes_dir() / f"{episode_id}.md")
        entry.transcripts_file = str(Config.get_transcript_path(episode_id))
        
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
            updated_data = entry.model_dump()
            updated_data.update(kwargs)
            self.entries[self.entries.index(entry)] = PodcastEntry.model_validate(updated_data)
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