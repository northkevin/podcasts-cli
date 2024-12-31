from typing import List
import logging
from abc import ABC, abstractmethod

from ..models.schemas import TranscriptData, Timestamp

logger = logging.getLogger(__name__)

class TranscriptProcessor(ABC):
    @abstractmethod
    def process(self, content: str) -> TranscriptData:
        """Process raw transcript content into structured data"""
        pass

class YouTubeTranscriptProcessor(TranscriptProcessor):
    def process(self, content: List[dict]) -> TranscriptData:
        """Process YouTube transcript format"""
        timestamps = []
        
        for item in content:
            timestamps.append(
                Timestamp(
                    start=item['start'],
                    end=item['start'] + item['duration'],
                    text=item['text']
                )
            )
            
        return TranscriptData(timestamps=timestamps)

class VimeoTranscriptProcessor(TranscriptProcessor):
    def process(self, content: str) -> TranscriptData:
        """Process Vimeo VTT format"""
        timestamps = []
        lines = content.splitlines()
        
        # Find start of content (skip headers)
        start_idx = next((i for i, line in enumerate(lines) if line.strip() == ""), 0) + 1
        
        current_time = None
        current_text = []
        
        for line in lines[start_idx:]:
            line = line.strip()
            
            if '-->' in line:
                # Save previous entry if exists
                if current_time and current_text:
                    start, end = self._parse_timestamp(current_time)
                    timestamps.append(
                        Timestamp(
                            start=start,
                            end=end,
                            text=' '.join(current_text)
                        )
                    )
                    current_text = []
                
                current_time = line
                
            elif line and not line.isdigit():
                current_text.append(line)
        
        # Add final entry
        if current_time and current_text:
            start, end = self._parse_timestamp(current_time)
            timestamps.append(
                Timestamp(
                    start=start,
                    end=end,
                    text=' '.join(current_text)
                )
            )
            
        return TranscriptData(timestamps=timestamps)
    
    def _parse_timestamp(self, timestamp: str) -> tuple[float, float]:
        """Parse VTT timestamp into start/end seconds"""
        start, end = timestamp.split(' --> ')
        
        def to_seconds(time_str: str) -> float:
            h, m, s = time_str.split(':')
            return float(h) * 3600 + float(m) * 60 + float(s)
            
        return to_seconds(start), to_seconds(end)

class TranscriptService:
    def __init__(self):
        self.processors = {
            'youtube': YouTubeTranscriptProcessor(),
            'vimeo': VimeoTranscriptProcessor()
        }
    
    def process_transcript(self, platform: str, content: str | List[dict]) -> TranscriptData:
        """Process transcript content based on platform"""
        processor = self.processors.get(platform)
        if not processor:
            raise ValueError(f"Unsupported platform: {platform}")
            
        try:
            return processor.process(content)
        except Exception as e:
            logger.error(f"Failed to process {platform} transcript: {e}")
            raise 