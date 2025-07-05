#!/usr/bin/env python3
"""
Script to list all available days for download from the MRO data server.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from datetime import datetime


def parse_directory_listing(html_content):
    """
    Parse the HTML directory listing to extract directory names (dates).
    
    Args:
        html_content (str): HTML content of the directory listing
        
    Returns:
        list: List of directory names (dates) found
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    directories = []
    
    # Find all links in the pre tag
    pre_tag = soup.find('pre')
    if pre_tag:
        for link in pre_tag.find_all('a'):
            href = link.get('href')
            if href and href.endswith('/') and href != '../':
                # Remove trailing slash and check if it's a date format
                dir_name = href.rstrip('/')
                if len(dir_name) == 8 and dir_name.isdigit():
                    directories.append(dir_name)
    
    return sorted(directories)


async def list_available_days_async(base_url="http://72.233.250.83/data/ecam"):
    """
    List all available days for download using async/await.
    
    Args:
        base_url (str): Base URL for the data server
        
    Returns:
        list: List of available dates
    """
    console = Console()
    
    # Ensure base_url ends with a slash to avoid redirects
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    
    console.print(f"[bold blue]Fetching available days from MRO data server...[/bold blue]")
    console.print(f"[dim]URL: {base_url}[/dim]")
    
    try:
        # Get the directory listing
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, follow_redirects=True)
            response.raise_for_status()
            
            # Parse the HTML to get directory list
            dates = parse_directory_listing(response.text)
            
            if not dates:
                console.print(f"[yellow]No date directories found[/yellow]")
                return []
            
            console.print(f"[green]Found {len(dates)} available days[/green]")
            
            # Create table to display dates
            table = Table(title="Available Days for Download")
            table.add_column("Index", style="cyan", justify="right")
            table.add_column("Date", style="white")
            table.add_column("Formatted Date", style="green")
            table.add_column("Day of Week", style="yellow")
            
            for i, date in enumerate(dates, 1):
                try:
                    # Parse the date
                    parsed_date = datetime.strptime(date, '%Y%m%d')
                    formatted_date = parsed_date.strftime('%Y-%m-%d')
                    day_of_week = parsed_date.strftime('%A')
                    
                    table.add_row(
                        str(i),
                        date,
                        formatted_date,
                        day_of_week
                    )
                except ValueError:
                    # If date parsing fails, still show the raw date
                    table.add_row(
                        str(i),
                        date,
                        "Invalid format",
                        "Unknown"
                    )
            
            console.print()
            console.print(table)
            
            # Show summary
            console.print(f"\n[bold cyan]Summary:[/bold cyan]")
            console.print(f"Total available days: [green]{len(dates)}[/green]")
            
            if dates:
                earliest = min(dates)
                latest = max(dates)
                console.print(f"Date range: [cyan]{earliest}[/cyan] to [cyan]{latest}[/cyan]")
            
            return dates
        
    except httpx.RequestError as e:
        console.print(f"[red]Error accessing {base_url}: {e}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return []


def list_available_days(base_url="http://72.233.250.83/data/ecam/"):
    """
    Wrapper function to run the async list function.
    
    Args:
        base_url (str): Base URL for the data server
        
    Returns:
        list: List of available dates
    """
    return asyncio.run(list_available_days_async(base_url))


def main():
    parser = argparse.ArgumentParser(description="List all available days for download from MRO data server")
    parser.add_argument("--base-url", default="http://72.233.250.83/data/ecam/", 
                       help="Base URL for the data server")
    parser.add_argument("--output", help="Output file to save the list (optional)")
    
    args = parser.parse_args()
    
    console = Console()
    console.print(Panel.fit(
        f"[bold blue]MRO Data Day Lister[/bold blue]\n"
        f"Base URL: [cyan]{args.base_url}[/cyan]",
        title="Configuration"
    ))
    
    dates = list_available_days(args.base_url)
    
    if dates:
        if args.output:
            # Save to file if requested
            output_path = Path(args.output)
            try:
                with open(output_path, 'w') as f:
                    for date in dates:
                        f.write(f"{date}\n")
                console.print(f"\n[green]✓ Saved {len(dates)} dates to {output_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving to file: {e}[/red]")
        
        console.print(f"\n[bold green]✅ Found {len(dates)} available days[/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ No days found or error occurred.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 