from pathlib import Path
import logging

from ...config import Config
from .prompt import generate_analysis_prompt
from ..models.schemas import PodcastEntry

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def _format_transcript_link(self, entry: PodcastEntry) -> str:
        """Format transcript link in Obsidian style"""
        transcript_file = f"{entry.episode_id}_transcript.md"
        return f"[[{transcript_file}]]"

    def generate_episode_markdown(self, entry) -> Path:
        """Generate episode markdown file"""
        episode_path = Config.EPISODES_DIR / f"{entry.episode_id}.md"
        
        # Generate prompt
        prompt = generate_analysis_prompt(
            title=entry.title,
            podcast_name=entry.podcast_name,
            episode_id=entry.episode_id,
            share_url=entry.url,
            transcript_filename=entry.transcripts_file,
            platform_type=entry.platform,
            interviewee=entry.interviewee
        )
        
        # Format episode content
        content = [
            f"# {entry.title}",
            "",
            "## Metadata",
            f"- **Title**: {entry.title}",
            f"- **Podcast**: {entry.podcast_name}",
            f"- **Published**: {entry.published_at.strftime('%Y-%m-%d')}",
            "",
            "## Links",
            f"- [Share URL]({entry.url})",
            f"- Transcript: {self._format_transcript_link(entry)}",
            "",
            "## Interviewee",
            f"- **Name**: {entry.interviewee.name}",
            f"- **Profession**: {entry.interviewee.profession}",
            f"- **Organization**: {entry.interviewee.organization}",
            "",
            "---",
            "",
            "## ChatGPT Analysis",
            "",
            "> [!note] Paste the ChatGPT response below this line",
            "",
            "...paste here...",
            "",
            "---",
            "",
            "## ChatGPT Prompt",
            "",
            "> [!info] Use this prompt with the transcript to generate the analysis above",
            "",
            "```",
            prompt,
            "```"
        ]
        
        # Write to file
        with open(episode_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        logger.info(f"Generated episode markdown: {episode_path}")
        return episode_path
    