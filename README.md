# Podcasts CLI

A command-line tool for processing podcast transcripts and generating structured notes.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/podcasts-cli.git
cd podcasts-cli

# Install in development mode
pip install -e .
```

## Configuration

Create a `.env` file in the root directory:

```env
YOUTUBE_API_KEY=your_api_key_here
```

## Usage

```bash
# Add a new podcast
podcasts add-podcast --platform youtube --url "https://youtube.com/watch?v=..."

# Process a podcast
podcasts process-podcast --episode_id <episode_id>

# Cleanup a podcast
podcasts cleanup-podcast --episode_id <episode_id>
```