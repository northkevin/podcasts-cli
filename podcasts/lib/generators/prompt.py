from typing import Dict, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_analysis_prompt(
    title: str,
    podcast_name: str,
    episode_id: str,
    share_url: str,
    transcript_filename: str,
    platform_type: str,
    interviewee: Dict = None
) -> str:
    """Generate a ChatGPT prompt for podcast analysis in Obsidian format"""
    
    prompt = f"""Analyze this timestamped podcast transcript and generate a structured note. IMPORTANT: Read the ENTIRE transcript before beginning analysis.

FORMATTING REQUIREMENTS:
- Use #tags for topics and themes
- Use **bold** for emphasis
- Include timestamps (HH:MM:SS) where relevant
- Maintain consistent list spacing

REQUIRED SECTIONS (in order):

1. QUOTES (EXACTLY 3)
Select quotes that represent:
- A paradigm-shifting statement
- An emotionally resonant insight
- A controversial claim
Format each as:
> [!quote]
> "Quote text" - Speaker (HH:MM:SS)
> #relevant-tags

NO CONTEXT OR IMPACT STATEMENT NEEDED - let quotes speak for themselves

2. OVERVIEW (2-3 SENTENCES ONLY)
- Core topic/thesis
- Unique perspective
- Key implications

3. CLAIMS (CRITICAL - 10 TARGET)
Each claim must be:
- Listed chronologically as they appear in transcript
- Balanced between all major themes of the episode
- Unique & substantial (no repetition)
- Supported by transcript evidence
- Tagged with #type and #topic
Aim for 10 claims - fewer only if transcript lacks substance

4. FLOW
Three key phases:
**Opening**: Initial context and foundational concepts
**Development**: Core arguments and evidence
**Conclusion**: Synthesis and implications

5. REFERENCES (ALL REQUIRED)
Books:
- **Title** by Author (Year)
  - Context: How/why mentioned (HH:MM:SS)
  #book #author-[lastname] #century-[xx]

People:
- **Name** - Role/Position (Year)
  - Contribution: Specific relevance (HH:MM:SS)
  #person #field-[area] #century-[xx]

Technologies:
- **[Name]**
  - Purpose: Brief description
  - Context: Role in discussion (HH:MM:SS)
  #technology #field-[area] #century-[xx]

6. TERMS
Define technical terms in order of appearance:
- **Term** [First mentioned at HH:MM:SS]
  - Definition: Clear explanation
  #technical-term

7. TAGS
#podcast #{platform_type} #[main-topic] #[secondary-topics]

VALIDATION CHECKLIST:
□ Read entire transcript first
□ 3 impactful quotes (paradigm-shift, emotional, controversial)
□ 10 claims (or justified fewer) in chronological order
□ ALL references with temporal context
□ Technical terms with first appearance time"""

    return prompt

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