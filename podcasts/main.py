#!/usr/bin/env python3

import os
import argparse
import logging
from typing import Optional

from .config import Config
from .lib.commands import cmd_add_podcast, cmd_process_podcast, cmd_cleanup_episode, cmd_configure, cmd_test_prompt

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
    process_parser.add_argument("--prompt-type", choices=["atomic", "standard"], 
                              default="atomic", help="Type of analysis prompt to use")
    
    # Cleanup podcast command
    cleanup_parser = subparsers.add_parser("cleanup-podcast")
    cleanup_parser.add_argument("--episode_id", required=True)
    
    # Config command
    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--obsidian", action="store_true", help="Configure Obsidian integration")
    config_parser.add_argument("--vault-path", help="Path to Obsidian vault")
    config_parser.add_argument("--episodes-dir", help="Episodes directory within vault")
    config_parser.add_argument("--transcripts-dir", help="Transcripts directory within vault")
    config_parser.add_argument("--reset", action="store_true", help="Reset to default configuration")
    
    # Add test command
    parser.add_argument(
        '--test-prompt',
        action='store_true',
        help='Generate a test prompt with sample metadata'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    # Ensure config is valid
    Config.ensure_dirs()
    
    # Execute command
    try:
        if args.test_prompt:
            cmd_test_prompt()
        elif args.command == "add-podcast":
            cmd_add_podcast(args.url, args.platform)
        elif args.command == "process-podcast":
            logger.debug(f"Processing podcast with args: episode_id={args.episode_id}, prompt_type={args.prompt_type}")
            cmd_process_podcast(args.episode_id, args.prompt_type)
        elif args.command == "cleanup-podcast":
            cmd_cleanup_episode(args.episode_id)
        elif args.command == "config":
            cmd_configure(args)
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(str(e))
        if args.debug:
            raise
        exit(1)

if __name__ == "__main__":
    main()