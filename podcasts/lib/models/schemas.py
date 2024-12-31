from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl

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