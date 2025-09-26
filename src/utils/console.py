"""Console utilities for the scraper."""
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Create custom theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "progress.percentage": "green",
    "progress.description": "cyan",
})

# Create console with custom theme
console = Console(theme=custom_theme)

def create_progress() -> Progress:
    """Create a rich progress bar."""
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )

def print_table(title: str, data: list, columns: list = None) -> None:
    """Print data in a rich table format."""
    table = Table(title=title)
    
    # If columns not provided, use keys from first data item
    if not columns and data:
        columns = list(data[0].keys())
    
    # Add columns to table
    for column in columns:
        table.add_column(column.replace('_', ' ').title())
    
    # Add rows to table
    for item in data:
        row = [str(item.get(col, "")) for col in columns]
        table.add_row(*row)
    
    console.print(table)

def print_summary(title: str, data: dict) -> None:
    """Print a summary panel with dictionary data."""
    content = "\n".join([f"{k}: {v}" for k, v in data.items()])
    panel = Panel(Text(content), title=title)
    console.print(panel)