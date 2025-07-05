#!/usr/bin/env python3
"""
Example usage of the MRO Data API and Display modules.

This script demonstrates how to use the separated MRODataAPI and MRODisplay classes.
"""

import asyncio
import sys
from pathlib import Path

# Add the scripts directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

from mro_api import MRODataAPI
from mro_display import MRODisplay


async def main():
    """Example usage of the separated API and Display modules."""
    
    # Initialize the API and Display
    api = MRODataAPI()
    display = MRODisplay()
    
    print("=== MRO Data API Example (Separated Concerns) ===\n")
    
    # Example 1: List all available days
    print("1. Listing all available days...")
    try:
        dates = await api.list_available_days()
        
        if dates:
            display.show_dates_found(len(dates))
            display.show_dates_table(dates)
            display.show_dates_summary(dates)
            
            # Example 2: Get files for a specific date
            if len(dates) > 0:
                sample_date = dates[0]  # Use the first available date
                print(f"\n2. Getting files for date {sample_date}...")
                
                files = await api.get_files_for_date(sample_date)
                if files:
                    print(f"Found {len(files)} FITS files for {sample_date}")
                    print("First 5 files:")
                    for i, file in enumerate(files[:5], 1):
                        print(f"  {i}. {file}")
                    if len(files) > 5:
                        print(f"  ... and {len(files) - 5} more files")
                else:
                    print(f"No files found for date {sample_date}")
            
            # Example 3: Download data for a specific date (commented out to avoid actual download)
            print(f"\n3. Example: Download data for date {sample_date}")
            print("(This is commented out to avoid actual download)")
            print("To actually download, uncomment the following lines:")
            print(f"""
            result = await api.download_date_data(
                date='{sample_date}',
                output_dir='data',
                force=False,
                max_concurrent=3
            )
            display.show_download_summary(result)
            if result["success"]:
                display.show_success_message()
            else:
                display.show_error_message(f"{{result['failed']}} files failed")
            """)
            
            # Example 4: Show how to use the convenience functions
            print("\n4. Using convenience functions:")
            print("   from mro_api import list_available_days, download_date_data")
            print("   dates = list_available_days()")
            print("   success = download_date_data('20250704')")
        
        else:
            display.show_error_message("No dates found or error occurred")
            
    except Exception as e:
        display.show_error_message(str(e))


def sync_example():
    """Example of using the API wrapper in synchronous code."""
    
    print("\n=== Synchronous Usage Example ===\n")
    
    # Import the convenience functions
    from mro_api import list_available_days, download_date_data
    
    # List available days
    print("Listing available days...")
    try:
        dates = list_available_days()
        
        if dates:
            print(f"Found {len(dates)} available days")
            print(f"First 5 dates: {dates[:5]}")
            
            # Example of downloading (commented out)
            print("\nTo download a specific date:")
            print("success = download_date_data('20250704', force=False, max_concurrent=5)")
        else:
            print("No dates found")
            
    except Exception as e:
        print(f"Error: {e}")


def demonstrate_separation():
    """Demonstrate the separation of concerns."""
    
    print("\n=== Separation of Concerns Demo ===\n")
    
    # API only - no display
    print("1. API-only usage (no display):")
    api = MRODataAPI()
    
    async def api_only():
        dates = await api.list_available_days()
        print(f"   Raw dates: {dates[:3]}...")  # Just print first 3
        return dates
    
    # Run the API-only example
    dates = asyncio.run(api_only())
    
    # Display only - using data from API
    print("\n2. Display-only usage:")
    display = MRODisplay()
    display.show_dates_table(dates)
    display.show_dates_summary(dates)
    
    print("\n3. Combined usage (as in the scripts):")
    # This is what the v2 scripts do
    display.show_configuration({"base_url": "http://72.233.250.83/data/ecam/"})
    display.show_dates_found(len(dates))
    display.show_success_message(f"Found {len(dates)} available days")


if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())
    
    # Run the sync example
    sync_example()
    
    # Demonstrate separation of concerns
    demonstrate_separation() 