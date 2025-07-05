#!/usr/bin/env python3
"""
Script to download all FITS files from a specific date from the MRO data server.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import time


def parse_directory_listing(html_content):
    """
    Parse the HTML directory listing to extract file names.
    
    Args:
        html_content (str): HTML content of the directory listing
        
    Returns:
        list: List of file names to download
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    files = []
    
    # Find all links in the pre tag
    pre_tag = soup.find('pre')
    if pre_tag:
        for link in pre_tag.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.fits'):
                files.append(href)
    
    return files


def download_file(url, local_path, chunk_size=8192):
    """
    Download a file with progress indication.
    
    Args:
        url (str): URL to download from
        local_path (str): Local path to save the file
        chunk_size (int): Chunk size for downloading
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Print progress
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rDownloading {os.path.basename(local_path)}: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        return True
        
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        return False


def download_date_data(date, base_url="http://72.233.250.83/data/ecam", output_dir="data", force=False):
    """
    Download all FITS files for a specific date.
    
    Args:
        date (str): Date in YYYYMMDD format
        base_url (str): Base URL for the data server
        output_dir (str): Output directory for downloaded files
        force (bool): Force re-download of existing files
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Create the URL for the date
    date_url = f"{base_url}/{date}/"
    
    # Create output directory
    date_dir = Path(output_dir) / date
    date_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching directory listing for {date}...")
    print(f"URL: {date_url}")
    
    try:
        # Get the directory listing
        response = requests.get(date_url)
        response.raise_for_status()
        
        # Parse the HTML to get file list
        files = parse_directory_listing(response.text)
        
        if not files:
            print(f"No FITS files found for date {date}")
            return False
        
        print(f"Found {len(files)} FITS files to download")
        
        # Statistics tracking
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        # Download each file
        for i, filename in enumerate(files, 1):
            file_url = urljoin(date_url, filename)
            local_path = date_dir / filename
            
            # Check if file already exists and is complete
            if local_path.exists() and not force:
                # Get expected file size from server
                try:
                    head_response = requests.head(file_url)
                    expected_size = int(head_response.headers.get('content-length', 0))
                    actual_size = local_path.stat().st_size
                    
                    if expected_size > 0 and actual_size == expected_size:
                        print(f"[{i}/{len(files)}] Skipping {filename} (already exists, size: {actual_size:,} bytes)")
                        skipped_count += 1
                        continue
                    else:
                        print(f"[{i}/{len(files)}] Re-downloading {filename} (incomplete file, expected: {expected_size:,}, actual: {actual_size:,})")
                except Exception as e:
                    print(f"[{i}/{len(files)}] Re-downloading {filename} (could not verify file size: {e})")
            
            print(f"[{i}/{len(files)}] Downloading {filename}...")
            if download_file(file_url, local_path):
                downloaded_count += 1
            else:
                failed_count += 1
            
            # Small delay to be nice to the server
            time.sleep(0.1)
        
        # Print summary
        print(f"\n" + "="*50)
        print(f"DOWNLOAD SUMMARY")
        print(f"="*50)
        print(f"Total files found: {len(files)}")
        print(f"Files downloaded: {downloaded_count}")
        print(f"Files skipped: {skipped_count}")
        print(f"Files failed: {failed_count}")
        print(f"Files saved to: {date_dir}")
        
        if failed_count == 0:
            print(f"\n✅ All files processed successfully!")
            return True
        else:
            print(f"\n⚠️  {failed_count} files failed to download.")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {date_url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download FITS files from MRO data server")
    parser.add_argument("date", help="Date in YYYYMMDD format (e.g., 20250704)")
    parser.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--base-url", default="http://72.233.250.83/data/ecam", 
                       help="Base URL for the data server")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-download of existing files")
    
    args = parser.parse_args()
    
    # Validate date format
    if not re.match(r'^\d{8}$', args.date):
        print("Error: Date must be in YYYYMMDD format (e.g., 20250704)")
        sys.exit(1)
    
    print(f"Starting download for date: {args.date}")
    print(f"Output directory: {args.output_dir}")
    print(f"Base URL: {args.base_url}")
    if args.force:
        print(f"Force mode: Will re-download existing files")
    print("-" * 50)
    
    success = download_date_data(args.date, args.base_url, args.output_dir, args.force)
    
    if success:
        print("\n✅ All files processed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some files failed to download.")
        sys.exit(1)


if __name__ == "__main__":
    main() 