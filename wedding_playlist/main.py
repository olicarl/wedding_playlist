#!/usr/bin/env python3
"""Main entry point for the wedding playlist application."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option()
def main():
    """Wedding Playlist Manager - Organize your perfect wedding music!"""
    pass


@main.command()
def list():
    """List all playlists."""
    table = Table(title="Wedding Playlists")
    table.add_column("Name", style="cyan")
    table.add_column("Songs", style="magenta")
    table.add_column("Duration", style="green")
    
    # Placeholder data
    table.add_row("Ceremony", "12", "45 min")
    table.add_row("Reception", "25", "1h 30min")
    table.add_row("First Dance", "3", "12 min")
    
    console.print(table)


@main.command()
@click.argument('name')
def create(name):
    """Create a new playlist."""
    console.print(f"✨ Created new playlist: [bold cyan]{name}[/bold cyan]")


@main.command()
@click.argument('playlist')
@click.argument('song')
def add(playlist, song):
    """Add a song to a playlist."""
    console.print(f"🎵 Added '[italic]{song}[/italic]' to [bold]{playlist}[/bold]")


if __name__ == "__main__":
    main() 