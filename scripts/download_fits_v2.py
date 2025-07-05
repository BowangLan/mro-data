#!/usr/bin/env python3
"""
Script to download all FITS files from a specific date from the MRO data server.
This version uses the separated API and display modules.
"""

import os
import re
import sys
import argparse
import asyncio
from pathlib import Path
from rich.console import Console
from rich import print as rprint

# Add the scripts directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

from mro_api import MRODataAPI
from mro_display import MRODisplay


async def main():
    parser = argparse.ArgumentParser(description="Download FITS files from MRO data server")
    parser.add_argument("date", help="Date in YYYYMMDD format (e.g., 20250704)")
    parser.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--base-url", default="http://72.233.250.83/data/ecam/", 
                       help="Base URL for the data server")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-download of existing files")
    parser.add_argument("--max-concurrent", type=int, default=5,
                       help="Maximum number of concurrent downloads (default: 5)")
    
    args = parser.parse_args()
    
    # Validate date format
    if not re.match(r'^\d{8}$', args.date):
        rprint("[red]Error: Date must be in YYYYMMDD format (e.g., 20250704)[/red]")
        sys.exit(1)
    
    # Validate max_concurrent
    if args.max_concurrent < 1:
        rprint("[red]Error: max_concurrent must be at least 1[/red]")
        sys.exit(1)
    
    # Initialize display and API
    console = Console()
    display = MRODisplay(console)
    api = MRODataAPI(args.base_url)
    
    # Show configuration
    display.show_configuration({
        "date": args.date,
        "output_dir": args.output_dir,
        "base_url": args.base_url,
        "force": args.force,
        "max_concurrent": args.max_concurrent
    })
    
    try:
        # Download the data
        result = await api.download_date_data(
            date=args.date,
            output_dir=args.output_dir,
            force=args.force,
            max_concurrent=args.max_concurrent
        )
        
        # Show results
        display.show_download_summary(result)
        
        if result["success"]:
            display.show_success_message()
            sys.exit(0)
        else:
            display.show_error_message(f"{result['failed']} files failed to download.")
            sys.exit(1)
            
    except Exception as e:
        display.show_error_message(str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 