import os
import logging
from pathlib import Path

from ..config import Config
from .models.podcast import PodcastList, save_state
from .models.schemas import Metadata
from .fetch.youtube import YouTubeFetcher
from .fetch.vimeo import get_vimeo_data_headless, create_episode_metadata, process_vimeo_transcript
from .generators.markdown import MarkdownGenerator
from .generators.id import IDGenerator

logger = logging.getLogger(__name__)

def cmd_add_podcast(url: str, platform: str) -> None:
    """Add new podcast to master list"""
    try:
        podcast_list = PodcastList()
        
        # Check if URL exists
        existing_entry = next((entry for entry in podcast_list.entries if entry.url == url), None)
        if existing_entry:
            print("\nPodcast already exists:")
            print(f"Episode ID: {existing_entry.episode_id}")
            print(f"Title: {existing_entry.title}")
            print(f"Podcast: {existing_entry.podcast_name}")
            print(f"Interviewee: {existing_entry.interviewee.name}")
            print(f"Status: {existing_entry.status}")
            print(f"Process Command: {existing_entry.process_command}")
            
            if input("\nWould you like to overwrite this entry? (y/N): ").lower() != 'y':
                print("Operation cancelled.")
                return
            
            existing_id = existing_entry.episode_id
            podcast_list.entries.remove(existing_entry)
        else:
            existing_id = None
        
        # Get metadata based on platform
        if platform == "youtube":
            fetcher = YouTubeFetcher(api_key=os.getenv('YOUTUBE_API_KEY'))
            metadata = fetcher.get_video_data(url)
        elif platform == "vimeo":
            data = get_vimeo_data_headless(url)
            metadata = create_episode_metadata(data.get("playerConfig", {}).get("video", {}).get("id"), data)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Add entry to podcast list
        entry = podcast_list.add_entry(url, platform, metadata, existing_id)
        
        print("\nPodcast added successfully!")
        print(f"Episode ID: {entry.episode_id}")
        print(f"Title: {entry.title}")
        print(f"Podcast: {entry.podcast_name}")
        print(f"Interviewee: {entry.interviewee.name}")
        print(f"\nRun next command:")
        print(f"{entry.process_command}")
        
    except Exception as e:
        logger.error(f"Error adding podcast: {e}")
        raise

def cmd_process_podcast(episode_id: str) -> None:
    """Process podcast content"""
    try:
        podcast_list = PodcastList()
        markdown_gen = MarkdownGenerator()
        
        entry = podcast_list.get_entry(episode_id)
        if not entry:
            raise ValueError(f"Episode {episode_id} not found")
        
        # Ensure directories exist
        Config.ensure_dirs()
        
        # Save initial state
        save_state(episode_id)
        
        try:
            # Generate transcript based on platform
            transcript_path = Config.get_transcript_path(entry.episode_id)
            
            if entry.platform == "youtube":
                fetcher = YouTubeFetcher(api_key=os.getenv('YOUTUBE_API_KEY'))
                transcript_data = fetcher.get_transcript(entry.url)
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_data.format())
            else:  # vimeo
                transcript_path = process_vimeo_transcript(entry)
            
            # Update transcript file path
            podcast_list.update_entry(episode_id, transcripts_file=str(transcript_path))
            
            # Generate episode markdown
            episode_file = markdown_gen.generate_episode_markdown(entry)
            podcast_list.update_entry(episode_id, episodes_file=str(episode_file))
            
            # Final state update
            save_state(episode_id, status="complete")
            
            print("\nProcessing completed successfully!")
            print(f"\nFiles created:")
            print(f"1. Episode:    {episode_file}")
            print(f"2. Transcript: {transcript_path}")
            print(f"\nPodcast data stored in: {Config.PODCAST_LIST}")
            print(f"Episode ID: {entry.episode_id}")
            
        except Exception as e:
            save_state(episode_id, status="error", error=str(e))
            podcast_list.update_entry(episode_id, status="error")
            raise
        
    except Exception as e:
        logger.error(f"Error processing podcast: {e}")
        raise

def cmd_cleanup_episode(episode_id: str) -> None:
    """Clean up all files for an episode and remove from database"""
    try:
        podcast_list = PodcastList()
        entry = podcast_list.get_entry(episode_id)
        
        if not entry:
            print(f"No episode found with ID: {episode_id}")
            return
        
        # Remove files if they exist
        for file_path in [entry.episodes_file, entry.claims_file, entry.transcripts_file]:
            if file_path:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    print(f"Removed: {path}")
        
        # Remove entry and reset ID cache
        podcast_list.entries.remove(entry)
        podcast_list._save()
        IDGenerator().reset_cache()
        
        print(f"\nCleanup completed successfully!")
        print(f"Removed episode: {entry.title}")
        print(f"Episode ID: {episode_id}")
        print(f"Removed from database: {Config.PODCAST_LIST}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise 