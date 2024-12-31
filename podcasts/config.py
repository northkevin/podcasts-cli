from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent
    DIST_DIR = BASE_DIR / "dist"
    
    # Content directories
    EPISODES_DIR = DIST_DIR / "episodes"
    TRANSCRIPTS_DIR = DIST_DIR / "transcripts"
    
    # State files
    PODCAST_LIST = DIST_DIR / "podcast_list.json"

    # File extensions and formats
    TRANSCRIPT_FILE_EXT = ".md"
    TRANSCRIPT_CODE_BLOCK = "timestamp-transcript"
    
    @classmethod
    def ensure_dirs(cls):
        """Create all necessary directories"""
        dirs = [
            cls.DIST_DIR,
            cls.EPISODES_DIR,
            cls.TRANSCRIPTS_DIR,
        ]
        
        for dir in dirs:
            if not dir.exists():
                dir.mkdir(parents=True)
                logger.debug(f"Created directory: {dir}") 

    @classmethod
    def get_transcript_path(cls, episode_id: str) -> Path:
        """Get standardized transcript path"""
        return cls.TRANSCRIPTS_DIR / f"{episode_id}_transcript{cls.TRANSCRIPT_FILE_EXT}"
    
# Create directories when module is imported
Config.ensure_dirs() 