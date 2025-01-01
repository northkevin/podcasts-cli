import os
import json
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open, MagicMock

from podcasts.lib.fetch.youtube import YouTubeFetcher
from podcasts.lib.models.base import Speaker, YouTubeMetadata
from podcasts.lib.models.podcast_config import PodcastConfig

# Mock YouTube API service document
MOCK_YOUTUBE_API = {
    "rootUrl": "https://www.googleapis.com/",
    "servicePath": "youtube/v3/",
    "resources": {
        "videos": {
            "methods": {
                "list": {
                    "path": "videos",
                    "httpMethod": "GET",
                    "parameters": {
                        "part": {"type": "string"},
                        "id": {"type": "string"}
                    }
                }
            }
        }
    }
}

# Mock API response data
MOCK_VIDEO_RESPONSE = {
    'items': [{
        'id': 'test_video_id',
        'snippet': {
            'title': 'Test Video',
            'description': 'Test Description',
            'channelId': 'UC123456789',
            'channelTitle': 'Test Channel',
            'publishedAt': '2024-01-01T00:00:00Z',
            'thumbnails': {
                'default': {
                    'url': 'https://i.ytimg.com/vi/test_video_id/default.jpg',
                    'width': 120,
                    'height': 90
                },
                'high': {
                    'url': 'https://i.ytimg.com/vi/test_video_id/hqdefault.jpg',
                    'width': 480,
                    'height': 360
                }
            },
            'tags': ['test', 'video']
        },
        'contentDetails': {
            'duration': 'PT1H30M'
        }
    }]
}

# Test data
MOCK_CONFIG = {
    "test_channel": {
        "channel_id": "UC123456789",
        "name": "Test Podcast",
        "host": {
            "name": "Test Host",
            "title": "Dr.",
            "role": "Host"
        },
        "default_tags": ["science", "technology"]
    }
}

@pytest.fixture
def mock_youtube_client():
    """Mock YouTube API client"""
    mock_client = MagicMock()
    
    # Setup the videos().list() chain
    mock_videos = MagicMock()
    mock_list = MagicMock()
    mock_client.videos.return_value = mock_videos
    mock_videos.list.return_value = mock_list
    mock_list.execute.return_value = MOCK_VIDEO_RESPONSE
    
    with patch('googleapiclient.discovery.build', return_value=mock_client):
        yield mock_client

@pytest.fixture
def youtube_fetcher(mock_youtube_client):
    """Create YouTubeFetcher with mock client"""
    with patch.object(YouTubeFetcher, '_load_podcast_configs', return_value=MOCK_CONFIG):
        fetcher = YouTubeFetcher("dummy_key")
        return fetcher

def test_config_based_speaker_extraction(youtube_fetcher):
    """Test speaker extraction using configs"""
    snippet = {
        'title': 'Amazing Interview with Guest Name',
        'description': 'A great conversation...',
        'channelId': 'UC123456789',  # Must match config's channel_id
        'channelTitle': 'Test Channel'
    }
    channel = {'snippet': {'title': 'Test Channel'}}
    
    host, guest = youtube_fetcher._extract_speakers(snippet, channel)
    assert host.name == "Test Host"  # Should match config
    assert host.title == "Dr."       # Should match config
    assert host.role == "Host"
    assert guest.name == "Amazing Interview..."  # Match truncation in code
    assert guest.role == "Guest"

def test_unconfigured_channel(youtube_fetcher):
    """Test speaker extraction for unconfigured channel"""
    snippet = {
        'title': 'Very Long Title That Should Be Truncated For Unknown Channel',
        'description': 'Some description...',
        'channelId': 'UNKNOWN123',
        'channelTitle': 'Unknown Channel'
    }
    channel = {'snippet': {'title': 'Unknown Channel'}}
    
    host, guest = youtube_fetcher._extract_speakers(snippet, channel)
    assert host.name == "Unknown Channel"
    assert host.role == "Host"
    assert guest.name == "Very Long Title T..."
    assert guest.role == "Guest"

def test_preset_tags(youtube_fetcher):
    """Test preset tag generation"""
    youtube_metadata = YouTubeMetadata(
        channel_id='UC123456789',
        channel_title='Test Channel',
        channel_url='https://youtube.com/c/test',
        video_id='abc123',
        category_id='27',
        tags=['science', 'education']
    )
    
    snippet = {
        'tags': ['science', 'education'],
        'categoryId': '27'
    }
    
    tags = youtube_fetcher._generate_preset_tags(snippet, youtube_metadata)
    assert 'science' in tags
    assert 'education' in tags

@pytest.mark.integration
def test_real_api_call():
    """Integration test with real YouTube API"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        pytest.skip("YOUTUBE_API_KEY environment variable not set")
    
    with patch.object(YouTubeFetcher, '_load_podcast_configs', return_value={}):
        fetcher = YouTubeFetcher(api_key)
        metadata = fetcher.get_video_data("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert metadata.title
        assert metadata.youtube_metadata.channel_id 