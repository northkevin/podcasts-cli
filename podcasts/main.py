#!/usr/bin/env python3

import os
import argparse
import logging
from typing import Optional

from .config import Config
from lib.commands import cmd_add_podcast, cmd_process_podcast, cmd_cleanup_episode

logger = logging.getLogger(__name__)

def setup_logging(debug: bool = False):
    """Configure logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Podcast processing tools")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command")
    
    # Add podcast command
    add_parser = subparsers.add_parser("add-podcast")
    add_parser.add_argument("--platform", required=True, choices=["youtube", "vimeo"])
    add_parser.add_argument("--url", required=True)
    
    # Process podcast command
    process_parser = subparsers.add_parser("process-podcast")
    process_parser.add_argument("--episode_id", required=True)
    
    # Cleanup podcast command
    cleanup_parser = subparsers.add_parser("cleanup-podcast")
    cleanup_parser.add_argument("--episode_id", required=True)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    # Ensure config is valid
    Config.ensure_dirs()
    
    # Execute command
    try:
        if args.command == "add-podcast":
            cmd_add_podcast(args.url, args.platform)
        elif args.command == "process-podcast":
            cmd_process_podcast(args.episode_id)
        elif args.command == "cleanup-podcast":
            cmd_cleanup_episode(args.episode_id)
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(str(e))
        if args.debug:
            raise
        exit(1)

if __name__ == "__main__":
    main()