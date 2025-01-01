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
    video_id = metadata.url.split("v=")[-1]
    url_base = f"https://youtube.com/watch?v={video_id}&t="
    
    # Format preset tags if available
    preset_tags_str = ""
    if metadata.preset_tags:
        preset_tags_str = "\nSuggested tags:\n" + "\n".join(
            f"- #{tag}" for tag in metadata.preset_tags
        )
    
    # Add note about config status
    config_status = ""
    if metadata.youtube_metadata and metadata.youtube_metadata.channel_id in fetcher.configs:
        config_status = "\n✓ Using configured podcast metadata"
    else:
        config_status = "\n⚠️ Using default metadata - configure in podcast_configs.json for better results"
    
    prompt = f"""ANALYZE PODCAST TRANSCRIPT
- Title: {metadata.title}
- Podcast: {metadata.formatted_podcast_name}
- Host: {metadata.host.name if metadata.host else 'Unknown'}
- Guest: {metadata.guest.get_speaker_attribution() if metadata.guest else 'Unknown'}{config_status}
- Duration: 00:00:00 to {end}

### GOAL
Create **at least {min_cards}** atomic notecards in Ryan Holiday's style - each focused on a single powerful quote or insight. Think of each card as a future building block for writing or thinking.

### NOTECARD FORMAT
> [!note] Notecard #{{{{ number }}}}
> [{{{{ HH:MM:SS }}}}]({url_base}{{{{ 1h2m3s format }}}})
> 
> "{{{{ powerful quote or key insight }}}}"
> - {metadata.guest.name if metadata.guest else 'Guest'} [or "{metadata.formatted_podcast_name}"]
> 
> #{{{{ mainCategory }}}}/{{{{ subCategory }}}} #{{{{ additionalTags }}}}

### TIMESTAMP FORMAT
- Display format: [HH:MM:SS]
- URL format: Add timestamp in 1h2m3s format
- Examples:
  - [00:05:30] -> {url_base}5m30s
  - [01:15:45] -> {url_base}1h15m45s
  - [02:00:00] -> {url_base}2h

### KEY PRINCIPLES
1. **Quote Selection**
   - Choose quotes that stand alone as powerful insights
   - Focus on timeless wisdom over contextual discussion
   - Capture surprising or counterintuitive ideas

2. **Formatting**
   - Top: Timestamp as YouTube link
   - Middle: The quote (the star of the show)
   - Bottom: Speaker attribution and tags
   - Tags: Use hierarchical format (#main/sub)

3. **Cross-References**
   - If ideas connect: "See card #X for related insight"
   - If claims conflict: "Contradicts card #X"
   - Keep these brief and only when truly valuable

### REVIEW PASS
After creating initial cards:
1. Remove any redundant cards
2. Ensure each quote is powerful enough to stand alone
3. Verify all timestamps and speaker attributions
4. Check tag consistency (#main/sub format)

### FINAL CHECKBOXES
- "[ ] I confirm at least {min_cards} atomic notecards produced"
- "[ ] I confirm each card captures a standalone insight"
- "[ ] I confirm all cards follow the exact format specified"

### SPEAKER ATTRIBUTION
When attributing quotes, use this priority:
1. Known speaker name (e.g., "{metadata.guest.name if metadata.guest else 'Guest'}")
2. Podcast name with episode (e.g., "{metadata.formatted_podcast_name}")
3. Channel name (e.g., "{metadata.youtube_metadata.channel_title if metadata.youtube_metadata else ''}")

\\#podcast-analysis \\#transcripts \\#{metadata.platform_type}-podcast"""

    return {"notecard_analysis": prompt}

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