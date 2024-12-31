from typing import Dict, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

from ..models.schemas import Interviewee

logger = logging.getLogger(__name__)

def generate_analysis_prompt(
    title: str,
    podcast_name: str,
    episode_id: str,
    share_url: str,
    transcript_filename: str,
    platform_type: str,
    interviewee: Interviewee,
    duration_seconds: int
) -> str:
    """Generate analysis prompt for podcast transcript"""
    
    # Calculate duration info
    end = format_timestamp(duration_seconds)
    duration_str = format_duration(duration_seconds)
    
    prompt = f"""ANALYZE PODCAST TRANSCRIPT: {title}

BEFORE STARTING:
1. Read the entire transcript ({transcript_filename}) from start to finish.
2. The total duration is {duration_str} (00:00:00 to {end}).
3. Confirm in your opening statement: "I have read the complete transcript from start to finish."

METADATA
- Title: {title}
- Podcast: {podcast_name}
- Guest: {interviewee.name}
- Role: {interviewee.profession}
- Organization: {interviewee.organization}

ANALYSIS STRUCTURE:

1. KEY QUOTES (4 total)
   - **One quote** from each quarter of the transcript, but do NOT label them as quarters
   - Simply present 4 quotes, each with a timestamp
   - Format in Markdown block-quote style:
     ```
     > [!quote]
     > "Quote text" – Speaker (HH:MM:SS)
     > #relevantTags
     ```

2. OVERVIEW (50-75 words maximum)
   - A succinct summary focusing on main topic(s), unique perspective(s), and why it matters.

3. CLAIMS (16-20 total)
   - Extract significant claims from across the entire episode
   - Each claim is in **one line**:
     ```
     Claim text (HH:MM:SS) #relevantTags
     ```

4. REFERENCES
   - **People**: Name, timestamp, why they were mentioned
   - **Books**: Title, timestamp, context/reason for mention
   - **Technologies**: Name, timestamp, function or relevance

5. TECHNICAL TERMS
   - **Term (HH:MM:SS)**: One-liner definition
   - Group related terms if appropriate

6. DEEP DIVE (if applicable)
   - **3–5 paragraphs** on the most significant or polarizing aspect of the conversation
   - If the episode is not especially deep or polarizing, you can omit this section

7. THEMES
   - Main themes and sub-themes
   - Use #mainThemes, #subTopics, etc., to keep the structure consistent

8. TAGS
   - Predefined: `#mainThemes #subTopics #keyFigures #technologies`
   - Add any others as relevant (e.g., #health #quantumMechanics #conspiracy)

CONFIRMATION
- [ ] "I confirm this analysis covers the entire podcast from 00:00:00 to {end}."
- [ ] Verify coverage of any named references or tangential mentions.

#podcast-analysis #transcripts #{platform_type}-podcast"""

    return prompt

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

def update_episode_markdown(
    episode_path: Path,
    gpt_response: Dict,
    transcript_path: Path,
    claims_path: Path
) -> str:
    """Generate updated episode markdown with GPT analysis
    
    Args:
        episode_path: Path to episode markdown file
        gpt_response: Parsed JSON response from ChatGPT
        transcript_path: Path to transcript file
        claims_path: Path to claims file
        
    Returns:
        str: Updated markdown content
    """
    
    # Convert paths to relative for Obsidian linking
    transcript_link = f"[[{transcript_path.name}]]"
    claims_link = f"[[{claims_path.name}]]"
    
    # Format interviewee section
    interviewee = gpt_response["interviewee"]
    interviewee_md = f"""## Interviewee
- **Name**: {interviewee['name']}
- **Profession**: {interviewee['profession']}
- **Organization**: {interviewee['organization']}
"""

    # Format summary
    summary_md = f"""## Summary
{gpt_response['summary']}
"""

    # Format related content
    related_md = f"""## Related Content
- Transcript: {transcript_link}
- Claims Analysis: {claims_link}
"""

    # Format metadata
    metadata_md = f"""## Metadata
### Topics
{', '.join(gpt_response['related_topics'])}

### Tags
{' '.join(['#' + tag for tag in gpt_response['tags']])}
"""

    # Combine sections
    markdown = f"""# {episode_path.stem}

{interviewee_md}

{summary_md}

{related_md}

{metadata_md}
"""

    return markdown

def format_claims_markdown(gpt_response: Dict) -> str:
    """Format claims analysis as markdown
    
    Args:
        gpt_response: Parsed JSON response from ChatGPT
        
    Returns:
        str: Formatted markdown for claims file
    """
    
    claims_md = ["# Claims Analysis\n"]
    
    # Group claims by filter type
    claims_by_filter = {}
    for claim in gpt_response["claims"]:
        filter_type = claim["filter"]
        if filter_type not in claims_by_filter:
            claims_by_filter[filter_type] = []
        claims_by_filter[filter_type].append(claim)
    
    # Format each section
    for filter_type, claims in claims_by_filter.items():
        claims_md.append(f"\n## {filter_type.title()}\n")
        for claim in claims:
            claims_md.append(f"### Claim {claim['claim_id']} ({claim['timestamp']})")
            claims_md.append(claim["claim"])
            claims_md.append(f"*Segment: {claim['segment']}*\n")
    
    return "\n".join(claims_md)

def save_prompt_to_episode(episode_path: Path, prompt: str):
    """Save the ChatGPT analysis section and prompt in the episode file
    
    Args:
        episode_path: Path to episode markdown file
        prompt: Generated prompt text
    """
    with open(episode_path, 'a') as f:
        # Add Analysis section first
        f.write("\n\n---\n")
        f.write("## ChatGPT Analysis\n\n")
        f.write("> [!note] Paste the ChatGPT response below this line\n\n")
        f.write("...paste here...\n\n")
        f.write("\n\n---\n\n")
        
        
        
        # Add Prompt section below
        f.write("## ChatGPT Prompt\n\n")
        f.write("> [!info] Use this prompt with the transcript to generate the analysis above\n\n")
        f.write("```\n")
        f.write(prompt)
        f.write("\n```\n")
        f.write("\n---\n") 