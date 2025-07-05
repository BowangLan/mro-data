#!/usr/bin/env python3
"""
Example usage of the download_fits.py script.
This demonstrates how to use the download functionality programmatically.
"""

import sys
from pathlib import Path

# Add the scripts directory to the path so we can import download_fits
sys.path.insert(0, str(Path(__file__).parent))

from download_fits import download_date_data


def main():
    """Example of downloading data for a specific date."""
    
    # Example: Download data for July 4, 2025
    date = "20250704"
    
    print("Example: Downloading MRO data for July 4, 2025")
    print("=" * 50)
    
    # Download the data
    success = download_date_data(
        date=date,
        base_url="http://72.233.250.83/data/ecam",
        output_dir="data",
        force=False  # Set to True to force re-download of existing files
    )
    
    if success:
        print(f"\n✅ Successfully downloaded all files for {date}")
        print(f"Files are saved in: data/{date}/")
    else:
        print(f"\n❌ Failed to download some files for {date}")


if __name__ == "__main__":
    main() 