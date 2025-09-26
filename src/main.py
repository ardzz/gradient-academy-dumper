"""Main entry point for the Gradient Academy Scraper."""
import argparse
import sys
import time
from pathlib import Path

from src.api.client import GradientClient
from src.db.manager import DatabaseManager
from src.scraper.courses import CourseScraper
from src.scraper.subchapters import SubchapterScraper
from src.utils.console import console, print_table, print_summary
from src.config import API_TOKEN, DB_PATH


def check_token():
    """Check if API token is available."""
    if not API_TOKEN:
        console.print("[bold red]Error:[/] API Token not found!")
        console.print("Please set the GRADIENT_API_TOKEN environment variable.")
        sys.exit(1)


def scrape_all():
    """Scrape all data from Gradient Academy."""
    start_time = time.time()
    
    with DatabaseManager() as db, GradientClient() as api:
        # Create scrapers
        course_scraper = CourseScraper(db, api)
        subchapter_scraper = SubchapterScraper(db, api)
        
        # Scrape courses and their content
        courses = course_scraper.scrape_courses()
        
        # Process each course
        for course in courses:
            course_slug = course.get('slug')
            content = course_scraper.scrape_course_content(course_slug)
            
            # Process each chapter in the course
            for chapter in content.get('chapters', []):
                chapter_id = chapter.get('chapter_id')
                subchapter_scraper.scrape_chapter_subchapters_with_details(course_slug, chapter_id)
    
    elapsed = time.time() - start_time
    console.print(f"[bold green]Scraping completed in {elapsed:.2f} seconds[/]")


def show_stats():
    """Show statistics from the database."""
    with DatabaseManager() as db:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chapters")
        chapter_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subchapters")
        subchapter_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lecturers")
        lecturer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        
        # Print statistics
        print_summary("Database Statistics", {
            "Courses": course_count,
            "Chapters": chapter_count,
            "Subchapters": subchapter_count,
            "Videos": video_count,
            "Lecturers": lecturer_count,
            "Books": book_count,
            "Database Path": DB_PATH
        })
        
        # List courses
        if course_count > 0:
            cursor.execute("""
                SELECT c.course_name, c.slug, 
                       COUNT(DISTINCT ch.id) as chapters, 
                       COUNT(DISTINCT s.id) as subchapters
                FROM courses c
                LEFT JOIN chapters ch ON c.id = ch.course_id
                LEFT JOIN subchapters s ON ch.id = s.chapter_id
                GROUP BY c.id
                ORDER BY c.course_name
            """)
            
            courses = [dict(row) for row in cursor.fetchall()]
            print_table("Courses", courses, ["course_name", "slug", "chapters", "subchapters"])


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Gradient Academy Scraper")
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--scrape', action='store_true', help='Scrape all data')
    args = parser.parse_args()
    
    console.print("[bold]Gradient Academy Scraper[/]")
    
    # Check if database exists
    db_exists = Path(DB_PATH).exists()
    
    if args.stats:
        if not db_exists:
            console.print("[yellow]Database doesn't exist yet. Run --scrape first.[/]")
        else:
            show_stats()
    elif args.scrape:
        check_token()
        scrape_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()