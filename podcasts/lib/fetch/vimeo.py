import logging
import datetime
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...config import Config
from ..models.schemas import Metadata, Interviewee, TranscriptData
from ..processors.transcript import TranscriptService

logger = logging.getLogger(__name__)

def get_vimeo_data_headless(url: str) -> dict:
    """Get Vimeo video data using headless browser"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        config_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-config-url]'))
        )
        
        config_url = config_element.get_attribute('data-config-url')
        response = requests.get(config_url)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to fetch Vimeo data: {str(e)}")
        raise ValueError(f"Could not get Vimeo data: {str(e)}")
        
    finally:
        if 'driver' in locals():
            driver.quit()

def create_episode_metadata(video_id: str, data: dict) -> Metadata:
    """Create episode metadata from Vimeo data"""
    video = data['video']
    owner = video.get('owner', {})
    
    return Metadata(
        title=video.get('title', ''),
        description=video.get('description', ''),
        published_at=datetime.fromtimestamp(video.get('upload_date', 0)),
        podcast_name=owner.get('name', ''),
        url=data.get('url', ''),
        interviewee=Interviewee(
            name=_extract_interviewee_name(video.get('title', '')),
            profession=_extract_profession(video.get('description', '')),
            organization=_extract_organization(video.get('description', ''))
        )
    )

def process_vimeo_transcript(entry) -> Path:
    """Process Vimeo transcript"""
    try:
        data = get_vimeo_data_headless(entry.url)
        metadata = data.get('request', {}).get('files', {}).get('captions', {})
        
        if not metadata or not metadata.get('webvtt'):
            raise ValueError("No transcript available")
            
        transcript_path = Config.get_transcript_path(entry.episode_id)
        
        # Get VTT content
        response = requests.get(metadata['webvtt']['url'])
        response.raise_for_status()
        vtt_content = response.text
        
        # Process transcript
        transcript_service = TranscriptService()
        transcript_data = transcript_service.process_transcript('vimeo', vtt_content)
        
        # Save formatted transcript
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_data.format())
        
        return transcript_path
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {str(e)}")
        raise

# Helper functions remain the same
def _extract_interviewee_name(title: str) -> str:
    if ' - ' in title:
        parts = title.split(' - ')
        return parts[1] if len(parts) > 2 else parts[-1]
    return title

def _extract_profession(description: str) -> str:
    prof_indicators = ['PhD', 'Dr.', 'Professor', 'CEO', 'Founder']
    for indicator in prof_indicators:
        if indicator.lower() in description.lower():
            return indicator
    return ""

def _extract_organization(description: str) -> str:
    if '(' in description and ')' in description:
        start = description.find('(') + 1
        end = description.find(')')
        return description[start:end]
    
    for line in description.split('\n')[:5]:
        if any(x in line.lower() for x in ['university', 'institute', 'organization', 'company']):
            return line.strip()
    return ""
