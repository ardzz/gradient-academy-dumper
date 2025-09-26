"""Subchapter scraper module."""
from typing import List, Dict, Any, Optional

from ..api.client import GradientClient
from ..db.manager import DatabaseManager
from ..utils.concurrency import run_with_concurrency_dict
from ..utils.console import console


class SubchapterScraper:
    """Scrapes subchapter data from Gradient Academy API."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, api_client: Optional[GradientClient] = None):
        """Initialize the subchapter scraper with db and api clients."""
        self.db = db_manager or DatabaseManager()
        self.api = api_client or GradientClient()
    
    def scrape_subchapters(self, chapter_id: str) -> List[Dict[str, Any]]:
        """Scrape all subchapters for a chapter."""
        try:
            console.print(f"[bold blue]Scraping subchapters for chapter:[/] {chapter_id}")
            subchapters = self.api.get_subchapters(chapter_id)
            
            if not subchapters:
                console.print("[yellow]No subchapters found.[/]")
                return []
            
            console.print(f"[green]Found {len(subchapters)} subchapters[/]")
            
            # Insert subchapters into database
            for subchapter in subchapters:
                subchapter_dict = subchapter.model_dump()
                self.db.insert_subchapter(subchapter_dict, chapter_id=chapter_id)
                console.print(f"[green]Saved subchapter:[/] {subchapter.subchapter_name}")
            
            return [subchapter.model_dump() for subchapter in subchapters]
            
        except Exception as e:
            console.print(f"[bold red]Error scraping subchapters:[/] {e}")
            return []
    
    def scrape_subchapter_detail(self, course_slug: str, subchapter_slug: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed information for a subchapter."""
        try:
            console.print(f"[bold blue]Scraping details for subchapter:[/] {subchapter_slug}")
            detail = self.api.get_subchapter_detail(course_slug, subchapter_slug)
            
            if not detail:
                console.print(f"[yellow]No details found for subchapter:[/] {subchapter_slug}")
                return None
            
            detail_dict = detail.model_dump()
            
            # Handle video if it exists
            if video := detail_dict.get('video'):
                self.db.insert_video(video, subchapter_id=detail.id)
                
                # Handle lecturers if they exist
                if lecturers := video.get('lecturers'):
                    for lecturer in lecturers:
                        self.db.insert_lecturer(lecturer)
                        self.db.insert_video_lecturer(video['id'], lecturer['id'])
            
            console.print(f"[green]Saved details for:[/] {subchapter_slug}")
            return detail_dict
            
        except Exception as e:
            console.print(f"[bold red]Error scraping subchapter detail:[/] {e}")
            return None
    
    def scrape_chapter_subchapters_with_details(self, course_slug: str, chapter_id: str) -> Dict[str, Any]:
        """Scrape all subchapters for a chapter with their details."""
        result = {
            "subchapters": [],
            "details": {}
        }
        
        # Get all subchapters
        subchapters = self.scrape_subchapters(chapter_id)
        result["subchapters"] = subchapters
        
        # Define a function to process a single subchapter
        def process_subchapter(subchapter):
            slug = subchapter.get("subchapter_slug")
            return slug, self.scrape_subchapter_detail(course_slug, slug)

        # Process subchapters concurrently
        if subchapters:
            console.print(f"[bold blue]Processing {len(subchapters)} subchapters concurrently[/]")
            details_dict = run_with_concurrency_dict(
                lambda s: process_subchapter(s),
                {i: s for i, s in enumerate(subchapters)},
                show_progress=True,
                description=f"Processing subchapters for chapter {chapter_id}"
            )

            # Convert results to the expected format
            for _, (slug, detail) in details_dict.items():
                if detail:
                    result["details"][slug] = detail

        return result
    
    def close(self):
        """Close connections."""
        self.api.close()
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()