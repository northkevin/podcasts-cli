import json
import logging
import re
from datetime import datetime

from ...config import Config

logger = logging.getLogger(__name__)

class IDGenerator:
    def __init__(self):
        self.cache_file = Config.DIST_DIR / "id_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load existing ID cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
                
        except Exception as e:
            logger.warning(f"Failed to load ID cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save current ID cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save ID cache: {e}")
    
    def generate_id(self, platform: str, published_at: datetime, interviewee_name: str) -> str:
        """Generate unique episode ID with interviewee name"""
        date_str = published_at.strftime("%y_%m_%d")
        
        # Clean and format interviewee name
        clean_name = self._clean_name(interviewee_name)
        
        # Create base ID with date, platform, and name
        base = f"{date_str}_{platform}_{clean_name}"
        
        # Get current count for this base
        count = self.cache.get(base, 0) + 1
        self.cache[base] = count
        
        # Save updated cache
        self._save_cache()

        # Format final ID
        return f"{base}_{count:02d}"
    
    def _clean_name(self, name: str) -> str:
        """Clean interviewee name for ID"""
        # Remove special characters and spaces
        clean = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        # Remove multiple underscores
        clean = re.sub(r'_+', '_', clean)
        # Take first two parts if name has multiple parts
        parts = clean.split('_')[:2]
        return '_'.join(parts)
    
    
    def reset_cache(self):
        """Reset ID cache"""
        self.cache = {}        
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("ID cache reset")
