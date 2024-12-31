# Podcast CLI Tool

A command-line tool for processing podcast episodes from YouTube and Vimeo, generating structured notes and transcripts for Obsidian.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/podcasts-cli.git
cd podcasts-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies and package
pip install -r requirements.txt
pip install -e .
```

## Environment Setup

Create a `.env` file in the root directory:
```bash
YOUTUBE_API_KEY=your_api_key_here
```

## Configuration

The CLI can output files to either a local dist directory (default) or your Obsidian vault.

```bash
# Show current configuration
podcasts config --show

# Configure for Obsidian (Interactive)
podcasts config --obsidian

# Configure for Obsidian (Direct)
podcasts config --obsidian \
  --vault-path "~/Documents/Obsidian/YourVault" \
  --episodes-dir "Podcasts/Episodes" \
  --transcripts-dir "Podcasts/Transcripts"

# Reset to default configuration
podcasts config --reset
```

## Usage

### 1. Add a Podcast Episode

```bash
# Add YouTube episode
podcasts add-podcast --platform youtube --url "https://www.youtube.com/watch?v=SiBFtwbyv44"

# Add Vimeo episode
podcasts add-podcast --platform vimeo --url "https://player.vimeo.com/video/1012842356?h=688d47c586"
```

### 2. Process a Podcast Episode
```bash
podcasts process-podcast --episode_id <EPISODE_ID>
```

### 3. Cleanup an Episode
```bash
podcasts cleanup-podcast --episode_id <EPISODE_ID>
```

## File Locations

### Default Mode
Files are saved to:
- Episodes: `podcasts/dist/episodes/`
- Transcripts: `podcasts/dist/transcripts/`
- Podcast List: `podcasts/dist/podcast_list.json`

### Obsidian Mode
Files are saved to your configured Obsidian vault:
- Episodes: `<vault_path>/<episodes_dir>/`
- Transcripts: `<vault_path>/<transcripts_dir>/`

## Testing Example

1. Start with default configuration:
```bash
podcasts config --reset
podcasts config --show
```

2. Add and process a YouTube episode:
```bash
podcasts add-podcast --platform youtube --url "https://www.youtube.com/watch?v=SiBFtwbyv44"
# Note the episode_id from output
podcasts process-podcast --episode_id <EPISODE_ID>
```

3. Configure for Obsidian:
```bash
podcasts config --obsidian --vault-path "~/Documents/Obsidian/TestVault"
```

4. Add and process a Vimeo episode:
```bash
podcasts add-podcast --platform vimeo --url "https://player.vimeo.com/video/1012842356?h=688d47c586"
# Note the episode_id from output
podcasts process-podcast --episode_id <EPISODE_ID>
```

## Debug Mode

Add `--debug` to any command for detailed logging:
```bash
podcasts --debug add-podcast --platform youtube --url "https://www.youtube.com/watch?v=SiBFtwbyv44"
```

## Development Requirements

- Python 3.9+
- YouTube API key (for YouTube videos)
- Selenium WebDriver (for Vimeo videos)

## Podcast Entry Fields

Each podcast entry contains:

- `episode_id`: Unique identifier for the episode
- `url`: URL to the podcast episode
- `platform`: Platform where the podcast is hosted (e.g., "youtube", "vimeo")
- `title`: Episode title
- `description`: Episode description
- `published_at`: Publication date
- `podcast_name`: Name of the podcast series
- `interviewee`: Information about the guest
- `duration_seconds`: Length of the podcast in seconds
- `status`: Processing status
- `episodes_file`: Path to episode markdown file
- `transcripts_file`: Path to transcript file