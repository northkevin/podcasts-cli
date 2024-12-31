import json
import logging
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
    
    def generate_id(self, platform: str, published_at: datetime) -> str:
        """Generate unique episode ID"""
        date_str = published_at.strftime("%y_%m_%d")
        base = f"{date_str}_{platform}"
        
        # Get current count for this base
        count = self.cache.get(base, 0) + 1
        self.cache[base] = count
        
        # Save updated cache
        self._save_cache()
        
        # Format final ID
        return f"{base}_{count:02d}"
    
    def reset_cache(self):
        """Reset ID cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("ID cache reset")