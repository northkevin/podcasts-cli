from typing import Dict, Optional
from pathlib import Path
import logging
from datetime import datetime

from ..models.schemas import Interviewee

logger = logging.getLogger(__name__)

def generate_atomic_prompts(
    title: str,
    podcast_name: str,
    episode_id: str,
    share_url: str,
    transcript_filename: str,
    platform_type: str,
    interviewee: Interviewee,
    duration_seconds: int,
    transcript_stats: dict = None,  # New parameter for transcript stats
    cards_per_hour: int = 5
) -> Dict[str, str]:
    """Generate atomic prompts for podcast analysis focusing on granular notecards"""
    
    # Calculate duration info
    end = format_timestamp(duration_seconds)
    duration_str = format_duration(duration_seconds)
    hours = duration_seconds / 3600
    min_cards = int(hours * cards_per_hour)
    
    # Format transcript stats if provided
    stats_str = ""
    if transcript_stats:
        stats_str = f"Approximate Transcript Size: ~{transcript_stats['words']:,} words / ~{transcript_stats['chars']:,} characters\n"
    
    prompt = f"""GRANULAR NOTECARDS PROMPT (Ryan Holiday–Style)
ANALYZE PODCAST TRANSCRIPT: {title}

METADATA (For reference and context):
Title: {title}
Podcast: {podcast_name}
Guest: {interviewee.name}
Role: {interviewee.profession}
Organization: {interviewee.organization}
Duration: {duration_str} (00:00:00 to {end})
{stats_str}Transcript File: {transcript_filename}

BEFORE YOU BEGIN
Read the entire transcript from 00:00:00 to {end} in full, before providing any output.

In your very first sentence, confirm you have done so, for example:
"I confirm I have read the entire transcript from start to finish."

Keep Both Detail and Context in Mind
- Focus on granular, atomic notecards (the "trees"), but remain aware of recurring themes and broader ideas (the "forest").

NOTECARD GENERATION
Goal: Produce atomized insights—quotes, claims, or anecdotes—similar to Ryan Holiday's physical note-card system, ensuring no major point is overlooked.

Notecards Per Hour
- For a {duration_str} podcast, create ~{cards_per_hour} notecards per hour, totaling at least {min_cards} notecards.
- If any segment is dense or significant, add additional notecards instead of skipping potentially important details.

Atomic Format
- One idea or quote per notecard—avoid grouping unrelated points.
- Each notecard must be an Obsidian callout of type "note".

Notecard Template
Use the following structure for each notecard:

```
> [!note] Notecard #{{{{ sequentialNumber }}}}
> **Theme/Tag(s):** #{{{{ mainTheme }}}} #{{{{ subTheme }}}} #{{{{ context }}}}
> **Timestamp:** HH:MM:SS
> **Key Idea/Quote:** "{{{{ direct quote or paraphrased idea }}}}" – {interviewee.name}
> **Significance/Use:** In 1–2 sentences, explain why this point matters or where it might be applied.
```

Formatting Notes:
- Always use "{interviewee.name}" as the speaker name for direct quotes.
- Include relevant sub-tags (e.g. #biology/quantum) for specialized topics.
- If a concept is mentioned at multiple timestamps, reference them accordingly.

Cross-References & Overarching Themes
Even though you are creating small, granular notes, remain mindful of connections:
- If you see repeated concepts or claims, cross-link them by saying "See also Notecard #X" or "Previously mentioned at HH:MM:SS."
- If you sense an overarching theme, highlight it briefly in "Theme/Tag(s)."

Avoid Omissions
- If you suspect a minor point might matter later (e.g., an anecdote, a tangential concept), create a separate notecard.
- If uncertain about relevance, include it—along with a timestamp—so the user can decide post-analysis.

REVIEW PASS (Second Pass)
After generating your initial set of notecards:

Double-Check for Missing Insights
- Revisit the transcript highlights: Did you capture every recurring idea, claim, or reference?
- If something was only vaguely referenced but might have deeper significance, add a notecard.

Ensure Cross-Links
- Confirm that repeated ideas/claims are consistently cross-referenced.
- If you notice contradictions, note them explicitly in each relevant notecard.

Maintain Context
- If any notecard's significance is unclear, expand its "Significance/Use" by 1–2 sentences.
- Indicate completion of this second pass at the end of your output.

CONFIRMATION & COMPLETENESS
After finalizing notecards and completing the review pass, include these checkboxes:
- "[ ] I confirm I have read the entire transcript from 00:00:00 to {end}."
- "[ ] I confirm all significant topics are captured in atomic notecards."
- "[ ] I confirm a second review pass was performed to ensure completeness and cross-links."

#podcast-analysis #transcripts #{platform_type}-podcast"""

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