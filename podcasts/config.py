from pathlib import Path
import os
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent
    DIST_DIR = BASE_DIR / "dist"
    
    # State files
    PODCAST_LIST = DIST_DIR / "podcast_list.json"
    CONFIG_FILE = DIST_DIR / "config.json"

    # File extensions and formats
    TRANSCRIPT_FILE_EXT = ".md"
    TRANSCRIPT_CODE_BLOCK = "timestamp-transcript"
    
    @classmethod
    def load_config(cls) -> dict:
        """Load configuration from file"""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        return {"use_obsidian": False}

    @classmethod
    def get_episodes_dir(cls) -> Path:
        """Get episodes directory (Obsidian or default)"""
        config = cls.load_config()
        
        if config.get("use_obsidian"):
            vault_path = Path(os.path.expanduser(config["obsidian_vault_path"]))
            return vault_path / config["episodes_dir"]
        return cls.DIST_DIR / "episodes"

    @classmethod
    def get_transcripts_dir(cls) -> Path:
        """Get transcripts directory (Obsidian or default)"""
        config = cls.load_config()
        
        if config.get("use_obsidian"):
            vault_path = Path(os.path.expanduser(config["obsidian_vault_path"]))
            return vault_path / config["transcripts_dir"]
        return cls.DIST_DIR / "transcripts"

    @classmethod
    def ensure_dirs(cls):
        """Create all necessary directories"""
        dirs = [
            cls.DIST_DIR,
            cls.get_episodes_dir(),
            cls.get_transcripts_dir(),
        ]
        
        for dir in dirs:
            if not dir.exists():
                dir.mkdir(parents=True)
                logger.debug(f"Created directory: {dir}")

    @classmethod
    def get_transcript_path(cls, episode_id: str) -> Path:
        """Get standardized transcript path"""
        return cls.get_transcripts_dir() / f"{episode_id}_transcript{cls.TRANSCRIPT_FILE_EXT}"

# Create directories when module is imported
Config.ensure_dirs() 