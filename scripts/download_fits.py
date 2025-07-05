#!/usr/bin/env python3
"""
Script to download all FITS files from a specific date from the MRO data server.
"""

import os
import re
import sys
import argparse
import asyncio
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint


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


async def download_file_with_progress(client, url, local_path, progress, task_id, chunk_size=8192):
    """
    Download a file with rich progress indication using httpx.
    
    Args:
        client (httpx.AsyncClient): HTTP client
        url (str): URL to download from
        local_path (str): Local path to save the file
        progress (Progress): Rich progress object
        task_id: Task ID for the progress bar
        chunk_size (int): Chunk size for downloading
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        async with client.stream('GET', url) as response:
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Update progress task with total size
            progress.update(task_id, total=total_size)
            
            with open(local_path, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress.update(task_id, completed=downloaded)
        
        return True
        
    except Exception as e:
        progress.console.print(f"[red]Error downloading {url}: {e}[/red]")
        return False


async def check_file_exists(url, local_path, force=False):
    """
    Check if a file already exists and is complete.
    
    Args:
        url (str): URL to check
        local_path (Path): Local file path
        force (bool): Force re-download
        
    Returns:
        tuple: (should_skip, reason)
    """
    if not local_path.exists() or force:
        return False, None
    
    try:
        async with httpx.AsyncClient() as client:
            head_response = await client.head(url)
            expected_size = int(head_response.headers.get('content-length', 0))
            actual_size = local_path.stat().st_size
            
            if expected_size > 0 and actual_size == expected_size:
                return True, f"already exists, size: {actual_size:,} bytes"
            else:
                return False, f"incomplete file, expected: {expected_size:,}, actual: {actual_size:,}"
    except Exception as e:
        return False, f"could not verify file size: {e}"


async def download_date_data_async(date, base_url="http://72.233.250.83/data/ecam", output_dir="data", force=False, max_concurrent=5):
    """
    Download all FITS files for a specific date using async/await.
    
    Args:
        date (str): Date in YYYYMMDD format
        base_url (str): Base URL for the data server
        output_dir (str): Output directory for downloaded files
        force (bool): Force re-download of existing files
        max_concurrent (int): Maximum number of concurrent downloads
        
    Returns:
        bool: True if successful, False otherwise
    """
    console = Console()
    
    # Create the URL for the date
    date_url = f"{base_url}/{date}/"
    
    # Create output directory
    date_dir = Path(output_dir) / date
    date_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]Fetching directory listing for {date}...[/bold blue]")
    console.print(f"[dim]URL: {date_url}[/dim]")
    
    try:
        # Get the directory listing
        async with httpx.AsyncClient() as client:
            response = await client.get(date_url)
            response.raise_for_status()
            
            # Parse the HTML to get file list
            files = parse_directory_listing(response.text)
            
            if not files:
                console.print(f"[yellow]No FITS files found for date {date}[/yellow]")
                return False
            
            console.print(f"[green]Found {len(files)} FITS files to download[/green]")
            console.print(f"[cyan]Using {max_concurrent} concurrent downloads[/cyan]")
            
            # Statistics tracking
            downloaded_count = 0
            skipped_count = 0
            failed_count = 0
            
            # Create progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                # Create main task for overall progress
                main_task = progress.add_task(
                    f"[cyan]Downloading {len(files)} files...", 
                    total=len(files)
                )
                
                # Create semaphore to limit concurrent downloads
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def download_single_file(filename, file_index):
                    """Download a single file with semaphore control."""
                    nonlocal downloaded_count, skipped_count, failed_count
                    
                    file_url = urljoin(date_url, filename)
                    local_path = date_dir / filename
                    
                    # Check if file already exists and is complete
                    should_skip, reason = await check_file_exists(file_url, local_path, force)
                    
                    if should_skip:
                        progress.console.print(f"[dim]Skipping {filename} ({reason})[/dim]")
                        skipped_count += 1
                        progress.advance(main_task)
                        return
                    elif reason:
                        progress.console.print(f"[yellow]Re-downloading {filename} ({reason})[/yellow]")
                    
                    # Create individual file task
                    file_task = progress.add_task(
                        f"[white]{filename}[/white]", 
                        total=None
                    )
                    
                    async with semaphore:
                        # Download the file
                        if await download_file_with_progress(client, file_url, local_path, progress, file_task):
                            downloaded_count += 1
                            progress.console.print(f"[green]✓ Downloaded {filename}[/green]")
                        else:
                            failed_count += 1
                            progress.console.print(f"[red]✗ Failed to download {filename}[/red]")
                    
                    # Remove the file task and advance main task
                    progress.remove_task(file_task)
                    progress.advance(main_task)
                
                # Create all download tasks
                tasks = [
                    download_single_file(filename, i) 
                    for i, filename in enumerate(files, 1)
                ]
                
                # Execute all downloads concurrently
                await asyncio.gather(*tasks)
            
            # Create summary table
            summary_table = Table(title="Download Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            summary_table.add_row("Total files found", str(len(files)))
            summary_table.add_row("Files downloaded", f"[green]{downloaded_count}[/green]")
            summary_table.add_row("Files skipped", f"[yellow]{skipped_count}[/yellow]")
            summary_table.add_row("Files failed", f"[red]{failed_count}[/red]")
            summary_table.add_row("Files saved to", str(date_dir))
            summary_table.add_row("Concurrent downloads", str(max_concurrent))
            
            console.print()
            console.print(summary_table)
            
            if failed_count == 0:
                console.print("\n[bold green]✅ All files processed successfully![/bold green]")
                return True
            else:
                console.print(f"\n[bold yellow]⚠️  {failed_count} files failed to download.[/bold yellow]")
                return False
        
    except httpx.RequestError as e:
        console.print(f"[red]Error accessing {date_url}: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return False


def download_date_data(date, base_url="http://72.233.250.83/data/ecam", output_dir="data", force=False, max_concurrent=5):
    """
    Wrapper function to run the async download function.
    
    Args:
        date (str): Date in YYYYMMDD format
        base_url (str): Base URL for the data server
        output_dir (str): Output directory for downloaded files
        force (bool): Force re-download of existing files
        max_concurrent (int): Maximum number of concurrent downloads
        
    Returns:
        bool: True if successful, False otherwise
    """
    return asyncio.run(download_date_data_async(date, base_url, output_dir, force, max_concurrent))


def main():
    parser = argparse.ArgumentParser(description="Download FITS files from MRO data server")
    parser.add_argument("date", help="Date in YYYYMMDD format (e.g., 20250704)")
    parser.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--base-url", default="http://72.233.250.83/data/ecam", 
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
    
    console = Console()
    console.print(Panel.fit(
        f"[bold blue]MRO Data Downloader[/bold blue]\n"
        f"Date: [cyan]{args.date}[/cyan]\n"
        f"Output: [cyan]{args.output_dir}[/cyan]\n"
        f"Base URL: [cyan]{args.base_url}[/cyan]\n"
        f"Force mode: [cyan]{'Yes' if args.force else 'No'}[/cyan]\n"
        f"Max concurrent: [cyan]{args.max_concurrent}[/cyan]",
        title="Configuration"
    ))
    
    success = download_date_data(args.date, args.base_url, args.output_dir, args.force, args.max_concurrent)
    
    if success:
        console.print("\n[bold green]✅ All files processed successfully![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Some files failed to download.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 