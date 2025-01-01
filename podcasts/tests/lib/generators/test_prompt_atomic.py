from datetime import datetime
from podcasts.lib.models.base import Speaker, YouTubeMetadata
from podcasts.lib.models.schemas import PodcastMetadata
from podcasts.lib.generators.prompt_atomic import generate_atomic_prompts

def test_prompt_with_thumbnail():
    """Test prompt generation with thumbnail"""
    metadata = PodcastMetadata(
        title="Test Podcast Episode",
        description="A great episode",
        published_at=datetime.now(),
        podcast_name="Test Podcast",
        url="https://youtube.com/watch?v=123",
        duration_seconds=3600,
        host=Speaker(name="Host Name"),
        guest=Speaker(name="Guest Name"),
        youtube_metadata=YouTubeMetadata(
            channel_id="123",
            channel_title="Test Channel",
            channel_url="https://youtube.com/c/test",
            video_id="123",
            category_id="27",
            thumbnail_url="https://i.ytimg.com/vi/123/maxresdefault.jpg"
        )
    )
    
    prompts = generate_atomic_prompts(metadata)
    assert "![[https://i.ytimg.com/vi/123/maxresdefault.jpg]]" in prompts["atomic_notes"] 