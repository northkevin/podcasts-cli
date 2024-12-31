from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, AnyHttpUrl, Field

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

class TranscriptData(BaseModel):
    timestamps: List[Timestamp]
    
    def format(self) -> str:
        """Format transcript in our standard format"""
        lines = ["# Transcript\n", "```timestamp-transcript"]
        
        for ts in self.timestamps:
            lines.extend([
                f"\n{ts.format()}",
                ts.text
            ])
            
        lines.append("\n```")
        return "\n".join(lines) 

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
    status: str = "pending"
    episodes_file: str = ""
    transcripts_file: str = ""
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
    
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
            webvtt_url=metadata.webvtt_url or "",
            status="pending"
        )