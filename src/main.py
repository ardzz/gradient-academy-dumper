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


def check_database():
    """Check if database exists."""
    if not Path(DB_PATH).exists():
        console.print("[bold red]Error:[/] Database not found!")
        console.print("Please run --scrape first to create the database.")
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
                LEFT JOIN chapters ch ON c.slug = ch.course_id
                LEFT JOIN subchapters s ON ch.id = s.chapter_id
                GROUP BY c.id
                ORDER BY c.course_name
            """)

            courses = [dict(row) for row in cursor.fetchall()]
            print_table("Courses", courses, ["course_name", "slug", "chapters", "subchapters"])


def download_videos(course_slug: str = None, output_path: str = None):
    """Download videos for a course."""
    from src.downloader.video import VideoDownloader

    with DatabaseManager() as db:
        downloader = VideoDownloader(db, output_path=output_path)

        if not course_slug:
            # List available courses with videos
            courses = downloader.list_available_courses()
            if not courses:
                console.print("[yellow]No courses with videos found in the database.[/]")
                return

            print_table("Available Courses", courses, ["course_name", "slug", "video_count"])

            # Ask user to select a course
            course_slug = console.input("\n[bold cyan]Enter course slug to download: [/]")
            if not course_slug:
                console.print("[yellow]No course selected. Exiting.[/]")
                return

        # Download the selected course videos
        downloader.download_course_videos(course_slug)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Gradient Academy Scraper")
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--scrape', action='store_true', help='Scrape all data')
    parser.add_argument('--download', action='store_true', help='Download videos from courses')
    parser.add_argument('--course', type=str, help='Course slug to download (optional)')
    parser.add_argument('--output', type=str, help='Output directory for downloads (optional)')
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
    elif args.download:
        if not db_exists:
            console.print("[yellow]Database doesn't exist yet. Run --scrape first.[/]")
        else:
            download_videos(args.course, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()