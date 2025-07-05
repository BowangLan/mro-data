#!/usr/bin/env python3
"""
MRO Data Server API Wrapper

This module provides a clean API interface for interacting with the MRO data server,
focusing only on server communication and data handling.
"""

import asyncio
import re
from pathlib import Path
from urllib.parse import urljoin
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

import httpx
from bs4 import BeautifulSoup


class MRODataAPI:
    """
    Clean API wrapper for the MRO data server.
    
    Focuses only on server communication and data handling,
    without any display or UI concerns.
    """
    
    def __init__(self, base_url: str = "http://72.233.250.83/data/ecam/"):
        """
        Initialize the MRO Data API wrapper.
        
        Args:
            base_url: Base URL for the MRO data server
        """
        # Ensure base_url ends with a slash to avoid redirects
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        
        self.base_url = base_url
    
    def _parse_directory_listing(self, html_content: str, file_type: str = "files") -> List[str]:
        """
        Parse HTML directory listing to extract file or directory names.
        
        Args:
            html_content: HTML content of the directory listing
            file_type: Type of items to extract ("files" or "directories")
            
        Returns:
            List of file or directory names
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        # Find all links in the pre tag
        pre_tag = soup.find('pre')
        if pre_tag:
            for link in pre_tag.find_all('a'):
                href = link.get('href')
                if not href:
                    continue
                
                if file_type == "files":
                    # Extract FITS files
                    if href.endswith('.fits'):
                        items.append(href)
                elif file_type == "directories":
                    # Extract date directories
                    if href.endswith('/') and href != '../':
                        dir_name = href.rstrip('/')
                        if len(dir_name) == 8 and dir_name.isdigit():
                            items.append(dir_name)
        
        return sorted(items) if file_type == "directories" else items
    
    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        """
        Make an HTTP request with proper error handling.
        
        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for httpx
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.RequestError: If the request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, follow_redirects=True, **kwargs)
            response.raise_for_status()
            return response
    
    async def list_available_days(self) -> List[str]:
        """
        List all available days for download.
        
        Returns:
            List of available dates in YYYYMMDD format
        """
        try:
            response = await self._make_request(self.base_url)
            dates = self._parse_directory_listing(response.text, "directories")
            return dates
            
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Error accessing {self.base_url}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    async def get_files_for_date(self, date: str) -> List[str]:
        """
        Get list of FITS files available for a specific date.
        
        Args:
            date: Date in YYYYMMDD format
            
        Returns:
            List of FITS file names
        """
        date_url = f"{self.base_url}{date}/"
        
        try:
            response = await self._make_request(date_url)
            files = self._parse_directory_listing(response.text, "files")
            return files
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Error accessing {date_url}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    async def check_file_exists(self, url: str, local_path: Path, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Check if a file already exists and is complete.
        
        Args:
            url: URL to check
            local_path: Local file path
            force: Force re-download
            
        Returns:
            Tuple of (should_skip, reason)
        """
        if not local_path.exists() or force:
            return False, None
        
        try:
            response = await self._make_request(url, method="HEAD")
            expected_size = int(response.headers.get('content-length', 0))
            actual_size = local_path.stat().st_size
            
            if expected_size > 0 and actual_size == expected_size:
                return True, f"already exists, size: {actual_size:,} bytes"
            else:
                return False, f"incomplete file, expected: {expected_size:,}, actual: {actual_size:,}"
        except Exception as e:
            return False, f"could not verify file size: {e}"
    
    async def download_file(self, url: str, local_path: Path, chunk_size: int = 8192) -> bool:
        """
        Download a file without progress indication.
        
        Args:
            url: URL to download from
            local_path: Local path to save the file
            chunk_size: Chunk size for downloading
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                            f.write(chunk)
            
            return True
            
        except Exception as e:
            return False
    
    async def download_date_data(self, date: str, output_dir: str = "data", 
                               force: bool = False, max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Download all FITS files for a specific date.
        
        Args:
            date: Date in YYYYMMDD format
            output_dir: Output directory for downloaded files
            force: Force re-download of existing files
            max_concurrent: Maximum number of concurrent downloads
            
        Returns:
            Dictionary with download statistics
        """
        # Create the URL for the date
        date_url = f"{self.base_url}{date}/"
        
        # Create output directory
        date_dir = Path(output_dir) / date
        date_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get the directory listing
            response = await self._make_request(date_url)
            files = self._parse_directory_listing(response.text, "files")
            
            if not files:
                return {
                    "success": False,
                    "downloaded": 0,
                    "skipped": 0,
                    "failed": 0,
                    "total": 0,
                    "output_dir": str(date_dir),
                    "error": "No FITS files found"
                }
            
            # Statistics tracking
            downloaded_count = 0
            skipped_count = 0
            failed_count = 0
            
            # Create semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_single_file(filename: str) -> Tuple[str, bool, str]:
                """Download a single file with semaphore control."""
                nonlocal downloaded_count, skipped_count, failed_count
                
                file_url = urljoin(date_url, filename)
                local_path = date_dir / filename
                
                # Check if file already exists and is complete
                should_skip, reason = await self.check_file_exists(file_url, local_path, force)
                
                if should_skip:
                    return filename, True, reason
                
                async with semaphore:
                    # Download the file
                    success = await self.download_file(file_url, local_path)
                    return filename, success, "downloaded" if success else "failed"
            
            # Create all download tasks
            tasks = [download_single_file(filename) for filename in files]
            
            # Execute all downloads concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for filename, success, reason in results:
                if isinstance(results, Exception):
                    failed_count += 1
                elif success:
                    if reason == "downloaded":
                        downloaded_count += 1
                    else:
                        skipped_count += 1
                else:
                    failed_count += 1
            
            result = {
                "success": failed_count == 0,
                "downloaded": downloaded_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "total": len(files),
                "output_dir": str(date_dir)
            }
            
            return result
        
        except httpx.RequestError as e:
            return {
                "success": False,
                "downloaded": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "output_dir": str(date_dir),
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "downloaded": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "output_dir": str(date_dir),
                "error": str(e)
            }


# Convenience functions for backward compatibility
def list_available_days(base_url: str = "http://72.233.250.83/data/ecam/") -> List[str]:
    """List all available days for download."""
    api = MRODataAPI(base_url)
    return asyncio.run(api.list_available_days())


def download_date_data(date: str, base_url: str = "http://72.233.250.83/data/ecam/", 
                      output_dir: str = "data", force: bool = False, max_concurrent: int = 5) -> bool:
    """Download all FITS files for a specific date."""
    api = MRODataAPI(base_url)
    result = asyncio.run(api.download_date_data(date, output_dir, force, max_concurrent))
    return result["success"] 