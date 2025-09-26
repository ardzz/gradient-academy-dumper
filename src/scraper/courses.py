"""Course scraper module."""
import time
from typing import List, Dict, Any, Optional

from ..api.client import GradientClient
from ..db.manager import DatabaseManager
from ..utils.concurrency import run_with_concurrency_dict
from ..utils.console import console


class CourseScraper:
    """Scrapes course data from Gradient Academy API."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, api_client: Optional[GradientClient] = None):
        """Initialize the course scraper with db and api clients."""
        self.db = db_manager or DatabaseManager()
        self.api = api_client or GradientClient()
    
    def scrape_courses(self) -> List[Dict[str, Any]]:
        """Scrape all available courses."""
        try:
            console.print("[bold blue]Scraping courses...[/]")
            courses = self.api.get_courses()
            
            if not courses:
                console.print("[yellow]No courses found.[/]")
                return []
            
            console.print(f"[green]Found {len(courses)} courses[/]")
            
            # Insert courses into database
            for course in courses:
                course_dict = course.model_dump()
                self.db.insert_course(course_dict)
                console.print(f"[green]Saved course:[/] {course.course_name}")
            
            return [course.model_dump() for course in courses]
            
        except Exception as e:
            console.print(f"[bold red]Error scraping courses:[/] {e}")
            return []
    
    def scrape_course_content(self, course_slug: str) -> Dict[str, Any]:
        """Scrape content for a specific course."""
        try:
            console.print(f"[bold blue]Scraping content for course:[/] {course_slug}")
            content = self.api.get_course_content(course_slug)
            
            result = {
                "chapters": [],
                "books": []
            }
            
            # Handle chapters
            for chapter in content.get("chapters", []):
                chapter_dict = chapter.model_dump()
                self.db.insert_chapter(chapter_dict, course_id=course_slug)
                result["chapters"].append(chapter_dict)
            
            # Handle books
            for book in content.get("books", []):
                self.db.insert_book(book, course_id=course_slug)
                result["books"].append(book)
            
            console.print(f"[green]Saved content for:[/] {course_slug}")
            return result
            
        except Exception as e:
            console.print(f"[bold red]Error scraping course content:[/] {e}")
            return {"chapters": [], "books": []}
    
    def scrape_all_course_content(self) -> Dict[str, Dict[str, Any]]:
        """Scrape content for all courses."""
        courses = self.scrape_courses()

        # Define processing function
        def process_course(course):
            slug = course.get("slug")
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
            return slug, self.scrape_course_content(slug)

        # Use concurrency for processing multiple courses
        console.print("[bold blue]Processing courses concurrently...[/]")
        results_dict = run_with_concurrency_dict(
            process_course,
            {i: course for i, course in enumerate(courses)},
            show_progress=True,
            description="Processing courses"
        )

        # Convert results to expected format
        result = {}
        for _, (slug, content) in results_dict.items():
            result[slug] = content

        return result
    
    def close(self):
        """Close connections."""
        self.api.close()
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()