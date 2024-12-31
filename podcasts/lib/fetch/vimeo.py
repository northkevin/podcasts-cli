import logging
import re
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...config import Config
from ..models.schemas import Metadata, Interviewee, TranscriptData, PodcastEntry

logger = logging.getLogger(__name__)

def _parse_ld_json(page_source: str) -> list:
    """Extract and parse ld+json data from page source."""
    pattern = r'<script type="application\/ld\+json">(.*?)<\/script>'
    matches = re.finditer(pattern, page_source, re.DOTALL)
    results = []
    
    for match in matches:
        try:
            data = json.loads(match.group(1))
            results.append(data)
        except json.JSONDecodeError:
            logger.warning("Failed to parse ld+json block")
            continue
            
    return results

def _extract_player_config(page_source: str) -> str:
    """Extract the JSON for window.playerConfig using balanced brace approach."""
    logger.debug("Using balanced brace approach for window.playerConfig.")

    start_match = re.search(r'window\.playerConfig\s*=\s*\{', page_source)
    if not start_match:
        logger.debug("No match for 'window.playerConfig = {' in page source.")
        raise ValueError("No window.playerConfig found.")

    start_index = start_match.end() - 1  # position of the '{'
    brace_count = 0
    end_index = None

    for i, ch in enumerate(page_source[start_index:], start=start_index):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i
                break

    if end_index is None:
        logger.debug("Couldn't find matching '}' for playerConfig.")
        raise ValueError("Could not find matching '}' for playerConfig JSON.")

    raw_json = page_source[start_index:end_index+1]
    logger.debug("Captured window.playerConfig (partial debug): %s", raw_json[:500])
    return raw_json

def get_vimeo_data_headless(vimeo_url: str) -> Dict[str, Any]:
    """Get Vimeo video data using headless browser."""
    logger.debug(f"Initializing headless browser to load: {vimeo_url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(vimeo_url)
        logger.debug("Waiting for page to load...")
        time.sleep(5)  # Increased wait time

        page_source = driver.page_source
        logger.debug("Page source received, length=%d", len(page_source))
        
        # Debug: Check if playerConfig exists
        if 'window.playerConfig' not in page_source:
            logger.error("playerConfig not found in page source")
            logger.debug("First 1000 chars of page source: %s", page_source[:1000])
            raise ValueError("Page didn't load properly - no playerConfig found")

        # Extract playerConfig
        raw_json = _extract_player_config(page_source)
        player_data = json.loads(raw_json)
        logger.debug("Successfully parsed window.playerConfig")

        # Extract LD+JSON data
        ld_json_list = _parse_ld_json(page_source)
        logger.debug("Found %d ld+json blocks", len(ld_json_list))

        return {
            "playerConfig": player_data,
            "ld_json": ld_json_list,
            "page_source": page_source,
            "url": vimeo_url  # Add the original URL
        }
    except Exception as e:
        logger.error(f"Failed to get Vimeo data: {str(e)}")
        logger.debug("URL attempted: %s", vimeo_url)
        raise
    finally:
        logger.debug("Quitting headless browser")
        driver.quit()

def create_episode_metadata(video_id: str, data: Dict) -> Metadata:
    """Create metadata from Vimeo data"""
    video = data.get("playerConfig", {}).get("video", {})
    
    # Extract duration in seconds from Vimeo data
    duration_raw = video.get("duration", 0)  # Vimeo provides duration in seconds
    duration_seconds = int(duration_raw)
    
    return Metadata(
        title=video.get("title", ""),
        description=video.get("description", ""),
        published_at=datetime.now(),  # Vimeo doesn't provide this easily
        podcast_name=extract_podcast_name(video),
        url=f"https://vimeo.com/{video_id}",
        interviewee=Interviewee(
            name=extract_interviewee_name(video),
            profession=extract_profession(video),
            organization=extract_organization(video)
        ),
        webvtt_url=extract_webvtt_url(data),
        duration_seconds=duration_seconds  # Add duration
    )

def process_vimeo_transcript(entry: PodcastEntry) -> Path:
    """Process Vimeo transcript using saved webvtt URL"""
    logger.debug(f"Processing transcript for {entry.episode_id}")
    
    if not entry.webvtt_url:
        raise ValueError("No transcript URL available for this video")
    
    try:
        # Get transcript content
        response = requests.get(entry.webvtt_url)
        response.raise_for_status()
        vtt_content = response.text
        
        # Save formatted transcript
        transcript_path = Config.get_transcript_path(entry.episode_id)
        logger.debug(f"Saving transcript to: {transcript_path}")
        
        formatted_lines = ["# Transcript\n"]
        formatted_lines.append(f"```{Config.TRANSCRIPT_CODE_BLOCK}")
        
        # Process VTT content
        lines = vtt_content.splitlines()
        start_idx = next((i for i, line in enumerate(lines) if line.strip() == ""), 0) + 1
        
        for line in lines[start_idx:]:
            line = line.strip()
            if '-->' in line:  # Timestamp line
                formatted_lines.append(f"\n[{line}]")
            elif line and not line.replace('-', '').isnumeric():
                formatted_lines.append(line)
        
        formatted_lines.append("\n```")
        
        # Write markdown file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_lines))
        
        return transcript_path
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {str(e)}")
        raise

# Helper functions remain the same
def _extract_interviewee_name(title: str) -> str:
    """Extract interviewee name from title."""
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

