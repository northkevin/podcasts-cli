import re
import json
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.errors import HttpError
from isodate import parse_duration

from ...config import Config
from ..models.schemas import (
    Metadata, 
    Interviewee, 
    TranscriptData, 
    TranscriptStats,
    Speaker,
    YouTubeMetadata
)
from ..processors.transcript import TranscriptService
from ..models.podcast_config import PodcastConfig, PodcastHost

logger = logging.getLogger(__name__)

class YouTubeFetcher:
    def __init__(self, api_key: str):
        logger.debug(f"Initializing YouTubeFetcher with API key: {api_key[:5]}...")
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key, cache_discovery=False)
            logger.debug("Successfully initialized YouTube API client")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {str(e)}")
            raise
            
        self.transcript_service = TranscriptService()
        self.configs = self._load_podcast_configs()
        logger.debug(f"Loaded {len(self.configs)} podcast configs")
    
    def _load_podcast_configs(self) -> dict:
        """Load podcast configurations"""
        config_path = Path(__file__).parent.parent.parent / "dist" / "podcast_configs.json"
        logger.debug(f"Looking for podcast configs at: {config_path}")
        if config_path.exists():
            try:
                configs = json.loads(config_path.read_text())
                logger.debug(f"Found {len(configs)} podcast configs")
                return configs
            except Exception as e:
                logger.error(f"Error loading podcast configs: {str(e)}")
                return {}
        logger.debug("No podcast configs found")
        return {}
    
    def _get_podcast_config(self, channel_id: str) -> Optional[PodcastConfig]:
        """Get podcast config by channel ID"""
        logger.debug(f"Looking for config with channel_id: {channel_id}")
        logger.debug(f"Available configs: {self.configs}")
        
        # The configs are nested under names, so we need to check each config's channel_id
        for config_data in self.configs.values():
            if isinstance(config_data, dict) and config_data.get('channel_id') == channel_id:
                logger.debug(f"Found matching config: {config_data}")
                return PodcastConfig(**config_data)
        
        logger.debug(f"No config found for channel_id: {channel_id}")
        return None
    
    def get_video_data(self, url: str) -> Metadata:
        """Get video metadata from YouTube"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            ).execute()
            
            if not response['items']:
                raise ValueError(f"No video found for ID: {video_id}")
            
            video_data = response['items'][0]
            snippet = video_data['snippet']
            channel_id = snippet['channelId']
            
            # Get best available thumbnail
            thumbnail_url = None
            if 'thumbnails' in snippet:
                thumbnails = snippet['thumbnails']
                # Try to get highest quality thumbnail
                for quality in ['maxres', 'high', 'medium', 'default']:
                    if quality in thumbnails:
                        thumbnail_url = thumbnails[quality]['url']
                        break
            
            # Get config if available
            config = self._get_podcast_config(channel_id)
            
            # Parse duration
            duration_iso = video_data['contentDetails']['duration']
            duration_seconds = int(parse_duration(duration_iso).total_seconds())
            
            # Extract speakers using config-aware method
            host, guest = self._extract_speakers(snippet, {'snippet': {'title': snippet['channelTitle']}})
            
            # Create interviewee from guest
            interviewee = Interviewee(
                name=guest.name,
                profession=self._extract_profession(snippet),
                organization=self._extract_organization(snippet)
            )

            # Create metadata with enhanced information
            metadata = Metadata(
                title=snippet['title'],
                description=snippet['description'],
                published_at=datetime.strptime(snippet['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                podcast_name=config.name if config else self._extract_podcast_name(snippet),
                url=url,
                host=host,
                guest=guest,
                interviewee=interviewee,
                webvtt_url="",
                duration_seconds=duration_seconds,
                youtube_metadata=YouTubeMetadata(
                    channel_id=channel_id,
                    channel_title=snippet['channelTitle'],
                    channel_url=f"https://youtube.com/channel/{channel_id}",
                    video_id=video_id,
                    category_id=snippet.get('categoryId', ''),
                    tags=snippet.get('tags', []),
                    thumbnail_url=thumbnail_url
                )
            )
            
            return metadata
            
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise ValueError(f"Failed to fetch video data: {str(e)}")
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        return ""
    
    def _extract_podcast_name(self, snippet: Dict) -> str:
        """Extract podcast name from video data"""
        channel_title = snippet.get('channelTitle', '')
        title = snippet.get('title', '')
        
        # Try to extract from title first
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        
        return channel_title
    
    def _extract_interviewee_name(self, snippet: Dict) -> str:
        """Extract interviewee name from video data"""
        title = snippet.get('title', '')
        
        # Look for patterns like "Name - Topic" or "Show - Name - Topic"
        if ' - ' in title:
            parts = title.split(' - ')
            return parts[1] if len(parts) > 2 else parts[-1]
            
        return title
    
    def _extract_profession(self, snippet: Dict) -> str:
        """Extract profession from video description"""
        description = snippet.get('description', '')
        
        # Look for common profession indicators
        prof_indicators = ['PhD', 'Dr.', 'Professor', 'CEO', 'Founder']
        for indicator in prof_indicators:
            if indicator.lower() in description.lower():
                return indicator
        
        return ""
    
    def _extract_organization(self, snippet: Dict) -> str:
        """Extract organization from video description"""
        description = snippet.get('description', '')
        
        # Look for organization in parentheses
        org_match = re.search(r'\((.*?)\)', description)
        if org_match:
            return org_match.group(1)
            
        # Look for organization in description
        desc_lines = description.split('\n')[:5]
        for line in desc_lines:
            if any(x in line.lower() for x in ['university', 'institute', 'organization', 'company']):
                return line.strip()
                
        return ""
    
    def get_transcript(self, url: str) -> TranscriptData:
        """Get transcript data from YouTube"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_data = TranscriptData(entries=transcript_list)
            
            # Calculate stats from text only (no timestamps)
            text_only = transcript_data.get_text_only()
            stats = TranscriptStats.from_text(text_only)
            transcript_data.stats = stats
            
            return transcript_data
            
        except Exception as e:
            logger.error(f"Error fetching transcript: {str(e)}")
            raise ValueError(f"Could not get transcript: {str(e)}")

    def _extract_speakers(self, snippet: Dict, channel: Optional[Dict]) -> Tuple[Optional[Speaker], Optional[Speaker]]:
        """Extract host and guest information using configs when available"""
        channel_id = snippet.get('channelId')
        logger.debug(f"Extracting speakers for channel_id: {channel_id}")
        
        config = self._get_podcast_config(channel_id) if channel_id else None
        logger.debug(f"Found config: {config}")
        
        if config and hasattr(config, 'host'):  # Check if config has host attribute
            logger.debug(f"Using configured host: {config.host}")
            # Use configured host
            host = Speaker(
                name=config.host.name,
                title=config.host.title,
                role=config.host.role
            )
        else:
            logger.debug("Using default channel title as host")
            # Default to channel name as host
            host = Speaker(
                name=channel['snippet']['title'] if channel else snippet['channelTitle'],
                role="Host"
            )
        
        # For guest, just use truncated title if no config
        title = snippet.get('title', '')
        if len(title) > 20:
            guest_name = f"{title[:17]}..."  # Consistently use 17 chars
        else:
            guest_name = title
            
        guest = Speaker(
            name=guest_name,
            role="Guest"
        )
        
        return host, guest

    def _generate_preset_tags(self, snippet: Dict, youtube_metadata: YouTubeMetadata) -> List[str]:
        """Generate preset tags from video data"""
        tags = set()
        
        # Add YouTube tags if available
        if youtube_metadata.tags:
            tags.update(tag.lower().replace(' ', '_') for tag in youtube_metadata.tags)
        
        # Add category-based tags
        category_map = {
            '27': 'education',
            '28': 'science_technology',
            '22': 'people_blogs',
            '24': 'entertainment'
        }
        if category_id := youtube_metadata.category_id:
            if category_tag := category_map.get(category_id):
                tags.add(category_tag)
        
        return sorted(list(tags))