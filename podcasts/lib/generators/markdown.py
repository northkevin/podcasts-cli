from pathlib import Path
import logging
import os

from ...config import Config
from .prompt import generate_analysis_prompt
from ..models.schemas import PodcastEntry

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def generate_episode_markdown(self, entry: PodcastEntry, prompt: str = None) -> Path:
        """Generate episode markdown file"""
        logger.info(f"Generating episode markdown for {entry.episode_id}")
        
        # Get file path
        episodes_dir = Config.get_episodes_dir()
        file_path = episodes_dir / f"{entry.episode_id}.md"
        
        # Format duration
        hours = entry.duration_seconds // 3600
        minutes = (entry.duration_seconds % 3600) // 60
        
        # Create markdown content
        content = [
            f"# {entry.title}\n",
            "## Metadata",
            f"- **Title**: {entry.title}",
            f"- **Podcast**: {entry.podcast_name}",
            f"- **Published**: {entry.published_at.strftime('%Y-%m-%d')}",
            f"- **Duration**: {hours}h {minutes}m\n",
            "## Links",
            f"- [Share URL]({entry.url})",
            f"- Transcript: [[{os.path.basename(entry.transcripts_file)}]]\n",
            "## Interviewee",
            f"- **Name**: {entry.interviewee.name}",
            f"- **Profession**: {entry.interviewee.profession}",
            f"- **Organization**: {entry.interviewee.organization}\n",
            "---\n",
            "## ChatGPT Analysis\n",
            "> [!note] Paste the ChatGPT response below this line\n",
            "...paste here...\n",
            "---\n",
            "## ChatGPT Prompt\n",
            "> [!info] Use this prompt with the transcript to generate the analysis above\n",
            "```",
            prompt if prompt else generate_analysis_prompt(
                title=entry.title,
                podcast_name=entry.podcast_name,
                episode_id=entry.episode_id,
                share_url=entry.url,
                transcript_filename=entry.transcripts_file,
                platform_type=entry.platform,
                interviewee=entry.interviewee,
                duration_seconds=entry.duration_seconds
            ),
            "```"
        ]
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
            
        logger.info(f"Generated episode markdown: {file_path}")
        return file_path
    