"""Video downloader for Gradient Academy videos."""
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..config import DOWNLOAD_PATH, FFMPEG_PATH
from ..db.manager import DatabaseManager
from ..utils.console import console, create_progress


class VideoDownloader:
    """Downloads videos from Gradient Academy."""

    def __init__(self, db_manager: DatabaseManager, output_path: Optional[str] = None):
        """Initialize video downloader."""
        self.db = db_manager
        self.output_path = Path(output_path) if output_path else DOWNLOAD_PATH
        self.output_path.mkdir(exist_ok=True, parents=True)
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run([FFMPEG_PATH, "-version"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if result.returncode != 0:
                console.print("[bold red]Warning:[/] ffmpeg not found or not working properly.")
                console.print("Please install ffmpeg or set the correct path in .env with FFMPEG_PATH.")
        except FileNotFoundError:
            console.print("[bold red]Error:[/] ffmpeg not found!")
            console.print("Please install ffmpeg or set the correct path in .env with FFMPEG_PATH.")

    def get_course_videos(self, course_slug: str) -> List[Dict[str, Any]]:
        """Get all videos for a specific course."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT c.course_name,
                                  ch.chapter_name,
                                  s.subchapter_name,
                                  v.id           as video_id,
                                  v.video_url,
                                  v.drm_video_url,
                                  v.token,
                                  v.drm_token,
                                  v.mux_playback_id,
                                  s.id           as subchapter_id,
                                  ch.order_index as chapter_order,
                                  s.order_index  as subchapter_order
                           FROM courses c
                                    JOIN chapters ch ON c.id = ch.course_id
                                    JOIN subchapters s ON ch.id = s.chapter_id
                                    JOIN videos v ON s.id = v.subchapter_id
                           WHERE c.slug = ?
                           ORDER BY ch.order_index, s.order_index
                           ''', (course_slug,))

            return [dict(row) for row in cursor.fetchall()]

    def list_available_courses(self):
        """List all courses with available videos."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT c.course_name,
                                  c.slug,
                                  COUNT(DISTINCT v.id) as video_count
                           FROM courses c
                                    JOIN chapters ch ON c.id = ch.course_id
                                    JOIN subchapters s ON ch.id = s.chapter_id
                                    JOIN videos v ON s.id = v.subchapter_id
                           GROUP BY c.id
                           ORDER BY c.course_name
                           ''')

            courses = [dict(row) for row in cursor.fetchall()]
            return courses

    def download_course_videos(self, course_slug: str):
        """Download all videos for a course."""
        videos = self.get_course_videos(course_slug)

        if not videos:
            console.print(f"[yellow]No videos found for course: {course_slug}[/]")
            return

        # Get course name from the first video
        course_name = videos[0].get('course_name')
        console.print(f"[bold green]Downloading {len(videos)} videos for:[/] {course_name}")

        # Create course directory
        course_dir = self.output_path / self._sanitize_filename(course_slug)
        course_dir.mkdir(exist_ok=True)

        # Download each video
        progress = create_progress()
        with progress:
            task = progress.add_task(f"[cyan]Downloading videos...", total=len(videos))

            for video in videos:
                chapter_name = video.get('chapter_name')
                subchapter_name = video.get('subchapter_name')
                chapter_order = video.get('chapter_order', 0)
                subchapter_order = video.get('subchapter_order', 0)

                # Create chapter directory
                chapter_dir_name = f"{chapter_order:02d}_{self._sanitize_filename(chapter_name)}"
                chapter_dir = course_dir / chapter_dir_name
                chapter_dir.mkdir(exist_ok=True)

                # Set the output filename
                filename = f"{subchapter_order:02d}_{self._sanitize_filename(subchapter_name)}.mp4"
                output_path = chapter_dir / filename

                # Skip if already downloaded
                if output_path.exists():
                    console.print(f"[yellow]Skipping existing file:[/] {output_path}")
                    progress.update(task, advance=1)
                    continue

                # Try to download
                success = self._download_video(video, output_path)

                if success:
                    console.print(f"[green]Downloaded:[/] {subchapter_name}")
                else:
                    console.print(f"[red]Failed to download:[/] {subchapter_name}")

                progress.update(task, advance=1)

        console.print(f"[bold green]Download complete! Videos saved to:[/] {course_dir}")

    def _download_video(self, video: Dict[str, Any], output_path: Path) -> bool:
        """Download a video using ffmpeg."""
        video_url = video.get('video_url')
        drm_video_url = video.get('drm_video_url')
        token = video.get('token')
        drm_token = video.get('drm_token')

        # First try with regular video_url if available
        if video_url:
            # For mux.com URLs, add the token
            if "stream.mux.com" in video_url and token:
                video_url = f"{video_url}?token={token}"

            try:
                cmd = [
                    FFMPEG_PATH,
                    "-y",  # Overwrite output files
                    "-i", video_url,
                    "-c", "copy",  # Copy without re-encoding
                    "-bsf:a", "aac_adtstoasc",
                    str(output_path)
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                if result.returncode == 0:
                    return True
            except Exception as e:
                console.print(f"[red]Error downloading video:[/] {e}")

        # If regular URL failed, try with DRM URL
        if drm_video_url and drm_token:
            try:
                url_with_token = f"{drm_video_url}?token={drm_token}"

                cmd = [
                    FFMPEG_PATH,
                    "-y",
                    "-i", url_with_token,
                    "-c", "copy",
                    "-bsf:a", "aac_adtstoasc",
                    str(output_path)
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                if result.returncode == 0:
                    return True
            except Exception as e:
                console.print(f"[red]Error downloading DRM video:[/] {e}")

        return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a string to be used as a filename."""
        return "".join(c for c in filename if c.isalnum() or c in ' ._-').strip()