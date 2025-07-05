#!/usr/bin/env python3
"""
Script to list all available days for download from the MRO data server.
This version uses the separated API and display modules.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from rich.console import Console

# Add the scripts directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

from mro_api import MRODataAPI
from mro_display import MRODisplay


async def main():
    parser = argparse.ArgumentParser(description="List all available days for download from MRO data server")
    parser.add_argument("--base-url", default="http://72.233.250.83/data/ecam/", 
                       help="Base URL for the data server")
    parser.add_argument("--output", help="Output file to save the list (optional)")
    parser.add_argument("--no-table", action="store_true", 
                       help="Don't display the formatted table")
    
    args = parser.parse_args()
    
    # Initialize display and API
    console = Console()
    display = MRODisplay(console)
    api = MRODataAPI(args.base_url)
    
    # Show configuration
    display.show_configuration({
        "base_url": args.base_url
    })
    
    try:
        # Show server info
        display.show_server_info(args.base_url)
        
        # List available days
        dates = await api.list_available_days()
        
        if dates:
            display.show_dates_found(len(dates))
            
            # Show table and summary if requested
            if not args.no_table:
                display.show_dates_table(dates)
                display.show_dates_summary(dates)
            
            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                try:
                    with open(output_path, 'w') as f:
                        for date in dates:
                            f.write(f"{date}\n")
                    display.show_save_success(str(output_path), len(dates))
                except Exception as e:
                    display.show_save_error(str(e))
            
            display.show_success_message(f"Found {len(dates)} available days")
            sys.exit(0)
        else:
            display.show_error_message("No days found or error occurred.")
            sys.exit(1)
            
    except Exception as e:
        display.show_error_message(str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 