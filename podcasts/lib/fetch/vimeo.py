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

def create_episode_metadata(video_id: str, data: Dict[str, Any]) -> Metadata:
    """Create episode metadata from Vimeo data"""
    logger.debug("Starting metadata creation for video_id: %s", video_id)
    
    # Extract domain from the input URL
    original_url = data.get("url", "")
    url_parts = urlparse(original_url)
    base_domain = f"{url_parts.scheme}://{url_parts.netloc}"
    logger.debug(f"Base domain: {base_domain}")

    # Get video data from playerConfig
    video_data = data.get("playerConfig", {}).get("video", {})
    if not video_data:
        logger.error("No video data found in playerConfig")
        logger.debug("playerConfig data: %s", json.dumps(data.get("playerConfig", {}), indent=2))
        raise ValueError("No video data found in Vimeo response")
    
    # Get transcript URL from text_tracks
    webvtt_url = None
    request_data = data.get("playerConfig", {}).get("request", {})
    logger.debug("Request data: %s", json.dumps(request_data, indent=2))
    
    if "text_tracks" in request_data and request_data["text_tracks"]:
        track = request_data["text_tracks"][0]
        track_url = track.get("url", "")
        logger.debug(f"Raw track URL: {track_url}")
        
        if track_url:
            # Fix URL formatting with proper domain
            track_url = track_url.lstrip('/')  # Remove leading slashes
            if not track_url.startswith(('http://', 'https://')):
                track_url = f"{base_domain}/{track_url}"  # Use original domain
            webvtt_url = str(track_url)  # Convert to string to ensure it's serializable
            logger.debug(f"Processed webvtt_url: {webvtt_url}")
    
    # Get LD+JSON data
    ld_json_data = next((item for item in data.get("ld_json", []) 
                        if item.get("@type") == "VideoObject"), {})
    
    # Extract title and try to parse interviewee info
    title = ld_json_data.get("name") or video_data.get('title', '')
    
    # Try to extract interviewee name from title
    interviewee_name = "<MANUAL>"
    if "PODCAST |" in title:
        # Format: "PODCAST | JACK KRUSE"
        parts = title.split("|")
        if len(parts) > 1:
            interviewee_name = parts[1].strip()
    elif "with" in title.lower():
        # Format: "Podcast with Jack Kruse"
        parts = title.lower().split("with")
        if len(parts) > 1:
            interviewee_name = parts[1].strip().title()
    
    # Get owner info for potential organization
    owner_data = video_data.get("owner", {})
    owner_name = owner_data.get("name", "")
    
    # Get upload date
    upload_date = (
        ld_json_data.get("uploadDate", "").split("T")[0] or
        video_data.get("upload_date") or
        datetime.now().strftime("%Y-%m-%d")
    )

    # Convert to datetime - handle both string and timestamp formats
    if isinstance(upload_date, str):
        published_at = datetime.fromisoformat(upload_date)
    else:
        # Assume it's a timestamp
        published_at = datetime.fromtimestamp(upload_date)
    
    metadata = Metadata(
        title=title,
        description=ld_json_data.get("description") or video_data.get('description', ''),
        published_at=published_at,
        podcast_name=owner_name,
        url=original_url,
        webvtt_url=webvtt_url,
        interviewee=Interviewee(
            name=interviewee_name,
            profession=_extract_profession(ld_json_data.get("description") or video_data.get('description', '')),
            organization=_extract_organization(ld_json_data.get("description") or video_data.get('description', ''))
        )
    )
    
    # Debug the final metadata
    logger.debug(f"Final metadata webvtt_url: {metadata.webvtt_url}")
    logger.debug(f"Full metadata: {metadata.model_dump_json(indent=2)}")
    
    return metadata

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

