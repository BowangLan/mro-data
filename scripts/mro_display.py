#!/usr/bin/env python3
"""
MRO Data Display Module

This module handles all display and UI concerns for MRO data operations,
separating presentation logic from the core API functionality.
"""

from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn


class MRODisplay:
    """
    Display handler for MRO data operations.
    
    Handles all UI/display concerns including progress bars, tables, and console output.
    """
    
    def __init__(self, console: Console = None):
        """
        Initialize the display handler.
        
        Args:
            console: Rich console instance (optional)
        """
        self.console = console or Console()
    
    def show_configuration(self, config: Dict[str, Any]) -> None:
        """Display configuration information."""
        self.console.print(Panel.fit(
            f"[bold blue]MRO Data Tool[/bold blue]\n"
            f"Base URL: [cyan]{config.get('base_url', 'N/A')}[/cyan]\n"
            f"Date: [cyan]{config.get('date', 'N/A')}[/cyan]\n"
            f"Output: [cyan]{config.get('output_dir', 'N/A')}[/cyan]\n"
            f"Force mode: [cyan]{'Yes' if config.get('force', False) else 'No'}[/cyan]\n"
            f"Max concurrent: [cyan]{config.get('max_concurrent', 'N/A')}[/cyan]",
            title="Configuration"
        ))
    
    def show_dates_table(self, dates: List[str]) -> None:
        """Display dates in a formatted table."""
        if not dates:
            self.console.print("[yellow]No date directories found[/yellow]")
            return
        
        table = Table(title="Available Days for Download")
        table.add_column("Index", style="cyan", justify="right")
        table.add_column("Date", style="white")
        table.add_column("Formatted Date", style="green")
        table.add_column("Day of Week", style="yellow")
        
        for i, date in enumerate(dates, 1):
            try:
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
                table.add_row(
                    str(i),
                    date,
                    "Invalid format",
                    "Unknown"
                )
        
        self.console.print()
        self.console.print(table)
    
    def show_dates_summary(self, dates: List[str]) -> None:
        """Display summary information about dates."""
        self.console.print(f"\n[bold cyan]Summary:[/bold cyan]")
        self.console.print(f"Total available days: [green]{len(dates)}[/green]")
        
        if dates:
            earliest = min(dates)
            latest = max(dates)
            self.console.print(f"Date range: [cyan]{earliest}[/cyan] to [cyan]{latest}[/cyan]")
    
    def show_download_progress(self, files: List[str], max_concurrent: int) -> Progress:
        """Create and return a progress bar for downloads."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console
        )
    
    def show_download_summary(self, result: Dict[str, Any]) -> None:
        """Display download summary table."""
        summary_table = Table(title="Download Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total files found", str(result.get("total", 0)))
        summary_table.add_row("Files downloaded", f"[green]{result.get('downloaded', 0)}[/green]")
        summary_table.add_row("Files skipped", f"[yellow]{result.get('skipped', 0)}[/yellow]")
        summary_table.add_row("Files failed", f"[red]{result.get('failed', 0)}[/red]")
        summary_table.add_row("Files saved to", result.get("output_dir", "N/A"))
        
        if "max_concurrent" in result:
            summary_table.add_row("Concurrent downloads", str(result["max_concurrent"]))
        
        self.console.print()
        self.console.print(summary_table)
    
    def show_success_message(self, message: str = "✅ All files processed successfully!") -> None:
        """Display success message."""
        self.console.print(f"\n[bold green]{message}[/bold green]")
    
    def show_error_message(self, message: str) -> None:
        """Display error message."""
        self.console.print(f"\n[bold red]❌ {message}[/bold red]")
    
    def show_warning_message(self, message: str) -> None:
        """Display warning message."""
        self.console.print(f"\n[bold yellow]⚠️  {message}[/bold yellow]")
    
    def show_info_message(self, message: str) -> None:
        """Display info message."""
        self.console.print(f"[blue]{message}[/blue]")
    
    def show_file_status(self, filename: str, status: str, reason: str = "") -> None:
        """Display individual file status."""
        if status == "skipped":
            self.console.print(f"[dim]Skipping {filename} ({reason})[/dim]")
        elif status == "downloaded":
            self.console.print(f"[green]✓ Downloaded {filename}[/green]")
        elif status == "failed":
            self.console.print(f"[red]✗ Failed to download {filename}[/red]")
        elif status == "redownloading":
            self.console.print(f"[yellow]Re-downloading {filename} ({reason})[/yellow]")
    
    def show_download_start(self, date: str, file_count: int, max_concurrent: int) -> None:
        """Display download start information."""
        self.console.print(f"[bold blue]Fetching directory listing for {date}...[/bold blue]")
        self.console.print(f"[green]Found {file_count} FITS files to download[/green]")
        self.console.print(f"[cyan]Using {max_concurrent} concurrent downloads[/cyan]")
    
    def show_server_info(self, url: str) -> None:
        """Display server information."""
        self.console.print(f"[bold blue]Fetching available days from MRO data server...[/bold blue]")
        self.console.print(f"[dim]URL: {url}[/dim]")
    
    def show_dates_found(self, count: int) -> None:
        """Display number of dates found."""
        self.console.print(f"[green]Found {count} available days[/green]")
    
    def show_save_success(self, filename: str, count: int) -> None:
        """Display file save success message."""
        self.console.print(f"\n[green]✓ Saved {count} dates to {filename}[/green]")
    
    def show_save_error(self, error: str) -> None:
        """Display file save error message."""
        self.console.print(f"[red]Error saving to file: {error}[/red]") 