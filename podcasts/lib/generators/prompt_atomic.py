import re
from typing import Dict
from ..models.schemas import PodcastMetadata

def generate_atomic_prompts(
    metadata: PodcastMetadata,
    transcript_stats: dict = None,
    cards_per_hour: int = 5
) -> Dict[str, str]:
    """Generate atomic prompts with config-aware metadata"""
    
    # Calculate duration info
    end = format_timestamp(metadata.duration_seconds)
    hours = metadata.duration_seconds / 3600
    min_cards = int(hours * cards_per_hour)
    
    # Generate timestamped URL format
    video_id = str(metadata.url).split("v=")[-1]
    url_base = f"https://youtube.com/watch?v={video_id}&t="
    
    # Add thumbnail if available
    thumbnail_section = ""
    if metadata.youtube_metadata and metadata.youtube_metadata.thumbnail_url:
        thumbnail_section = f"![[{metadata.youtube_metadata.thumbnail_url}]]\n\n"
    
    # Build the prompt
    prompt = f"""# {metadata.title}

{thumbnail_section}## Metadata
- **Guest**: {metadata.guest.name if metadata.guest else 'Unknown'}
- **Host**: {metadata.host.name if metadata.host else 'Unknown'}
- **Date**: {metadata.published_at.strftime('%Y-%m-%d')}
- **URL**: {metadata.url}
- **Duration**: {end}

## Description
{metadata.description}

## Notes
- Target: {min_cards} atomic notes minimum
- Focus on key concepts, insights, and unique perspectives
- Include relevant timestamps using format: {url_base}{{seconds}}
- Tag speakers appropriately
"""
    
    return {
        "atomic_notes": prompt
    }

def format_timestamp(seconds: int) -> str:
    """Format seconds into HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_duration(seconds: int) -> str:
    """Format duration in human readable form"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hours, {minutes} minutes"

def format_youtube_timestamp(seconds: int) -> str:
    """Format seconds into YouTube timestamp format (1h2m3s)"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # include seconds if it's the only value
        parts.append(f"{secs}s")
    
    return "".join(parts) 

def validate_youtube_timestamp(timestamp: str) -> bool:
    """Validate YouTube timestamp format (1h2m3s)"""
    # Pattern matches formats like 1h, 2m, 3s, 1h2m, 2m3s, 1h2m3s
    pattern = r'^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'
    
    if not timestamp:
        return False
        
    match = re.match(pattern, timestamp)
    if not match:
        return False
        
    # Ensure at least one value is present
    return any(g for g in match.groups() if g is not None)

def convert_timestamp_to_youtube(timestamp: str) -> str:
    """Convert HH:MM:SS to YouTube timestamp format"""
    hours, minutes, seconds = map(int, timestamp.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return format_youtube_timestamp(total_seconds) 