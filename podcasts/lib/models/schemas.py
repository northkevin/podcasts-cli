from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, AnyHttpUrl, Field, constr, field_serializer

from .base import Speaker, YouTubeMetadata

class Timestamp(BaseModel):
    start: float
    end: float
    text: str

    def format(self) -> str:
        """Format timestamp in HH:MM:SS.mmm format"""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}"
            
        return f"[{format_time(self.start)} --> {format_time(self.end)}]"

class Interviewee(BaseModel):
    name: str
    profession: str = ""
    organization: str = ""

class Metadata(BaseModel):
    title: str
    description: str
    published_at: datetime
    podcast_name: str
    interviewee: Interviewee
    url: HttpUrl
    webvtt_url: Optional[str] = ""
    duration_seconds: int
    host: Optional[Speaker] = None
    guest: Optional[Speaker] = None
    youtube_metadata: Optional[YouTubeMetadata] = None

class TranscriptStats(BaseModel):
    words: int
    chars: int

    @classmethod
    def from_text(cls, text: str) -> "TranscriptStats":
        """Create stats from transcript text"""
        return cls(
            words=len(text.split()),
            chars=len(text)
        )

class TranscriptData(BaseModel):
    entries: List[Dict[str, Any]]
    stats: Optional[TranscriptStats] = None
    
    def format(self) -> str:
        """Format transcript entries into markdown"""
        lines = ["# Transcript\n", "```timestamp-transcript"]
        
        for entry in self.entries:
            # Format timestamp
            start = entry.get('start', 0)
            duration = entry.get('duration', 0)
            end = start + duration
            
            timestamp = self._format_time_range(start, end)
            text = entry.get('text', '')
            
            lines.extend([
                f"\n{timestamp}",
                text
            ])
            
        lines.append("\n```")
        return "\n".join(lines)
    
    def _format_time_range(self, start: float, end: float) -> str:
        """Format time range in [HH:MM:SS.mmm --> HH:MM:SS.mmm] format"""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}"
            
        return f"[{format_time(start)} --> {format_time(end)}]"
    
    def get_text_only(self) -> str:
        """Get plain text without timestamps for stats calculation"""
        return "\n".join(entry.get('text', '') for entry in self.entries)

class PodcastEntry(BaseModel):
    episode_id: str
    url: str
    platform: str
    title: str
    description: str
    published_at: datetime
    podcast_name: str
    interviewee: Interviewee
    webvtt_url: Optional[str] = ""
    duration_seconds: int
    status: str = "pending"
    episodes_file: str = ""
    transcripts_file: str = ""
    
    @field_serializer('published_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        return dt.isoformat()
    
    @property
    def process_command(self) -> str:
        return f"python -m podcasts process-podcast --episode_id {self.episode_id} --prompt-type atomic"
    
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
            webvtt_url=metadata.webvtt_url or "",
            duration_seconds=metadata.duration_seconds,
            status="pending"
        )

class PodcastMetadata(BaseModel):
    """Enhanced podcast metadata"""
    title: str
    description: str
    published_at: datetime
    podcast_name: str  # e.g., "Danny Jones Podcast"
    episode_number: Optional[str] = None  # e.g., "Ep. 188"
    host: Optional[Speaker] = None
    guest: Optional[Speaker] = None
    url: HttpUrl
    webvtt_url: Optional[str] = ""
    duration_seconds: int
    youtube_metadata: Optional[YouTubeMetadata] = None
    preset_tags: List[str] = Field(default_factory=list)

    @property
    def formatted_podcast_name(self) -> str:
        """Format podcast name with episode number"""
        if self.episode_number:
            return f"{self.podcast_name} | {self.episode_number}"
        return self.podcast_name

    def get_speaker_attribution(self, timestamp: str = None) -> str:
        """Get speaker attribution in priority order"""
        if self.guest and self.guest.name:
            # Format guest name with title if available
            name_parts = []
            if self.guest.title:
                name_parts.append(self.guest.title)
            name_parts.append(self.guest.name)
            return " ".join(name_parts)
            
        if self.host and self.host.name:
            return f"{self.host.name} ({self.formatted_podcast_name})"
            
        if self.youtube_metadata:
            return self.youtube_metadata.short_title
            
        return self.title[:20] + "..."
