import os
import logging
from pathlib import Path
import json
import pyperclip

from ..config import Config
from .models.podcast import PodcastList, save_state
from .models.schemas import Metadata, Interviewee
from .fetch.youtube import YouTubeFetcher
from .fetch.vimeo import get_vimeo_data_headless, create_episode_metadata, process_vimeo_transcript
from .generators.markdown import MarkdownGenerator
from .generators.id import IDGenerator
from .generators.prompt import generate_analysis_prompt
from .generators.prompt_atomic import generate_atomic_prompts

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
            print(f"Duration: {existing_entry.duration_seconds // 3600}h {(existing_entry.duration_seconds % 3600) // 60}m")
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
        print(f"Duration: {entry.duration_seconds // 3600}h {(entry.duration_seconds % 3600) // 60}m")
        print(f"Podcast: {entry.podcast_name}")
        print(f"Interviewee: {entry.interviewee.name}")
        print(f"WebVTT URL: {entry.webvtt_url}")
        print(f"\nRun next command:")
        print(f"{entry.process_command}")
        
    except Exception as e:
        logger.error(f"Error adding podcast: {e}")
        raise

def cmd_process_podcast(episode_id: str) -> None:
    """Process a podcast episode"""
    try:
        # Get podcast entry
        podcast_list = PodcastList()
        markdown_gen = MarkdownGenerator()
        
        entry = podcast_list.get_entry(episode_id)
        if not entry:
            raise ValueError(f"No podcast found with ID: {episode_id}")

        # Get transcript and stats
        fetcher = YouTubeFetcher(api_key=os.getenv('YOUTUBE_API_KEY'))
        transcript_data = fetcher.get_transcript(entry.url)
        transcript_stats = transcript_data.stats.model_dump() if transcript_data.stats else None
        
        # Generate analysis prompt
        prompt = generate_atomic_prompts(
            title=entry.title,
            podcast_name=entry.podcast_name,
            episode_id=entry.episode_id,
            share_url=entry.url,
            transcript_filename=entry.transcripts_file,
            platform_type=entry.platform,
            interviewee=entry.interviewee,
            duration_seconds=entry.duration_seconds,
            transcript_stats=transcript_stats,
            cards_per_hour=5
        )

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
            elif entry.platform == "vimeo" and entry.webvtt_url:
                transcript_path = process_vimeo_transcript(entry)
            else:
                raise ValueError(f"Unsupported platform or missing webvtt_url: {entry.platform}")
            
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
            
        except Exception as e:
            save_state(episode_id, status="error", error=str(e))
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
        for file_path in [entry.episodes_file, entry.transcripts_file]:
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

def cmd_configure(args):
    """Configure CLI settings"""
    try:
        if args.show:
            config = Config.load_config()
            print("\nCurrent Configuration:")
            print("---------------------")
            print(f"Using Obsidian: {config.get('use_obsidian', False)}")
            if config.get('use_obsidian'):
                print(f"Vault Path: {config.get('obsidian_vault_path', 'Not set')}")
                print(f"Episodes Directory: {config.get('episodes_dir', 'Not set')}")
                print(f"Transcripts Directory: {config.get('transcripts_dir', 'Not set')}")
            print("\nCurrent Paths:")
            print(f"Episodes: {Config.get_episodes_dir()}")
            print(f"Transcripts: {Config.get_transcripts_dir()}")
            return

        if args.reset:
            if Config.CONFIG_FILE.exists():
                Config.CONFIG_FILE.unlink()
            print("Configuration reset to defaults")
            return

        config = Config.load_config()
        
        if args.obsidian:
            config["use_obsidian"] = True
            
            if args.vault_path:
                config["obsidian_vault_path"] = os.path.expanduser(args.vault_path)
            else:
                vault_path = input("Enter path to your Obsidian vault: ")
                config["obsidian_vault_path"] = os.path.expanduser(vault_path)
            
            if args.episodes_dir:
                config["episodes_dir"] = args.episodes_dir
            else:
                episodes_dir = input("Enter episodes directory name [Podcast Episodes]: ") or "Podcast Episodes"
                config["episodes_dir"] = episodes_dir
            
            if args.transcripts_dir:
                config["transcripts_dir"] = args.transcripts_dir
            else:
                transcripts_dir = input("Enter transcripts directory name [Podcast Transcripts]: ") or "Podcast Transcripts"
                config["transcripts_dir"] = transcripts_dir

        # Save configuration
        with open(Config.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
        print("\nConfiguration updated successfully!")
        print(f"Episodes directory: {Config.get_episodes_dir()}")
        print(f"Transcripts directory: {Config.get_transcripts_dir()}")
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise 

def cmd_test_prompt(episode_id: str = "test_123") -> None:
    """Generate a test prompt with sample metadata"""
    
    # Sample metadata for testing
    test_metadata = {
        "title": "Exiled Brain Surgeon: DARPA Mind Control, Quantum Biology & Sunlight Medicine | Dr. Jack Kruse",
        "podcast_name": "Danny Jones",
        "episode_id": episode_id,
        "share_url": "https://youtube.com/watch?v=test123",
        "transcript_filename": "transcripts/test_123_transcript.md",
        "platform_type": "youtube",
        "interviewee": {
            "name": "Dr. Jack Kruse",
            "profession": "Neurosurgeon / Researcher",
            "organization": "N/A"
        },
        "duration_seconds": 15360,  # 4 hours, 16 minutes
        "transcript_stats": {
            "words": 89536,
            "chars": 440646
        }
    }
    
    # Create Interviewee object
    interviewee = Interviewee(
        name=test_metadata["interviewee"]["name"],
        profession=test_metadata["interviewee"]["profession"],
        organization=test_metadata["interviewee"]["organization"]
    )
    
    # Generate prompt
    from .generators.prompt_atomic import generate_atomic_prompts
    prompts = generate_atomic_prompts(
        title=test_metadata["title"],
        podcast_name=test_metadata["podcast_name"],
        episode_id=test_metadata["episode_id"],
        share_url=test_metadata["share_url"],
        transcript_filename=test_metadata["transcript_filename"],
        platform_type=test_metadata["platform_type"],
        interviewee=interviewee,
        duration_seconds=test_metadata["duration_seconds"],
        transcript_stats=test_metadata["transcript_stats"],
        cards_per_hour=5
    )
    
    prompt = prompts["notecard_analysis"]
    
    # Print and copy to clipboard
    print("\n=== TEST PROMPT ===\n")
    print(prompt)
    print("\n=== END TEST PROMPT ===\n")
    
    try:
        pyperclip.copy(prompt)
        print("✓ Prompt copied to clipboard!")
    except Exception as e:
        print(f"! Could not copy to clipboard: {e}")
        print("Please copy the prompt manually from above.") 