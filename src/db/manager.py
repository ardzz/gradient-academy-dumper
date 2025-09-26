"""Database manager for the scraper."""
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from ..config import DB_PATH


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.db_path = db_path or DB_PATH
        self._local = threading.local()
        self._local.conn = None
        self.setup_database()
    
    def setup_database(self):
        """Set up database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.executescript('''
                -- Courses table
                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    cover_url TEXT,
                    thumbnail_url TEXT,
                    trailer_url TEXT,
                    is_free BOOLEAN,
                    is_coming_soon BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Chapters table
                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    chapter_name TEXT NOT NULL,
                    order_index INTEGER,
                    subchapter_counts INTEGER,
                    is_coming_soon BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                );

                -- Subchapters table
                CREATE TABLE IF NOT EXISTS subchapters (
                    id TEXT PRIMARY KEY,
                    chapter_id TEXT NOT NULL,
                    subchapter_name TEXT NOT NULL,
                    subchapter_slug TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    order_index INTEGER,
                    duration TEXT,
                    is_free BOOLEAN,
                    thumbnail_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                );

                -- Videos table
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    subchapter_id TEXT NOT NULL,
                    video_url TEXT,
                    drm_video_url TEXT,
                    token TEXT,
                    drm_token TEXT,
                    mux_playback_id TEXT,
                    duration TEXT,
                    description TEXT,
                    thumbnail_url TEXT,
                    is_free BOOLEAN,
                    is_drm_protected BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subchapter_id) REFERENCES subchapters (id)
                );

                -- Lecturers table
                CREATE TABLE IF NOT EXISTS lecturers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT,
                    photo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Video_Lecturers table
                CREATE TABLE IF NOT EXISTS video_lecturers (
                    video_id TEXT,
                    lecturer_id TEXT,
                    PRIMARY KEY (video_id, lecturer_id),
                    FOREIGN KEY (video_id) REFERENCES videos (id),
                    FOREIGN KEY (lecturer_id) REFERENCES lecturers (id)
                );

                -- Books table
                CREATE TABLE IF NOT EXISTS books (
                    slug TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    rating REAL,
                    book_cover_url TEXT,
                    authors TEXT,
                    category TEXT,
                    percentage_progress REAL,
                    course_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                );
            ''')
            
            conn.commit()
    
    def get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def close(self):
        """Close the database connection for the current thread."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def insert_course(self, course: Dict[str, Any]) -> bool:
        """Insert a course into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO courses 
                    (id, course_name, slug, cover_url, thumbnail_url, trailer_url, is_free, is_coming_soon)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course.get('id'),
                    course.get('course_name'),
                    course.get('slug'),
                    course.get('cover'),
                    course.get('thumbnail'),
                    course.get('trailer'),
                    course.get('is_free'),
                    course.get('is_coming_soon')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting course: {e}")
            return False
    
    def insert_chapter(self, chapter: Dict[str, Any], course_id: str) -> bool:
        """Insert a chapter into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO chapters 
                    (id, course_id, chapter_name, order_index, subchapter_counts, is_coming_soon)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    chapter.get('chapter_id'),
                    course_id,
                    chapter.get('chapter_name'),
                    chapter.get('order'),
                    chapter.get('subchapter_counts'),
                    chapter.get('is_coming_soon')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting chapter: {e}")
            return False
    
    def insert_subchapter(self, subchapter: Dict[str, Any], chapter_id: str) -> bool:
        """Insert a subchapter into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO subchapters 
                    (id, chapter_id, subchapter_name, subchapter_slug, type, order_index, 
                     duration, is_free, thumbnail_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    subchapter.get('id'),
                    chapter_id,
                    subchapter.get('subchapter_name'),
                    subchapter.get('subchapter_slug'),
                    subchapter.get('type'),
                    subchapter.get('order'),
                    subchapter.get('duration'),
                    subchapter.get('is_free'),
                    subchapter.get('thumbnail')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting subchapter: {e}")
            return False
    
    def insert_video(self, video: Dict[str, Any], subchapter_id: str) -> bool:
        """Insert a video into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (id, subchapter_id, video_url, drm_video_url, token, drm_token, mux_playback_id, duration, description, 
                     thumbnail_url, is_free, is_drm_protected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video.get('id'),
                    subchapter_id,
                    video.get('video_url'),
                    video.get('drm_video_url'),
                    video.get('token'),
                    video.get('drm_token'),
                    video.get('mux_playback_id'),
                    video.get('duration'),
                    video.get('description'),
                    video.get('thumbnail'),
                    video.get('is_free'),
                    video.get('is_drm_protected')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting video: {e}")
            return False
    
    def insert_lecturer(self, lecturer: Dict[str, Any]) -> bool:
        """Insert a lecturer into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO lecturers 
                    (id, name, role, photo_url)
                    VALUES (?, ?, ?, ?)
                ''', (
                    lecturer.get('id'),
                    lecturer.get('name'),
                    lecturer.get('role'),
                    lecturer.get('photo')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting lecturer: {e}")
            return False
    
    def insert_video_lecturer(self, video_id: str, lecturer_id: str) -> bool:
        """Insert a video-lecturer relation into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO video_lecturers 
                    (video_id, lecturer_id)
                    VALUES (?, ?)
                ''', (video_id, lecturer_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting video_lecturer: {e}")
            return False
    
    def insert_book(self, book: Dict[str, Any], course_id: str) -> bool:
        """Insert a book into the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO books 
                    (slug, title, rating, book_cover_url, authors, category, percentage_progress, course_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    book.get('slug'),
                    book.get('title'),
                    book.get('rating'),
                    book.get('book_cover_url'),
                    book.get('authors'),
                    book.get('category'),
                    book.get('percentage_progress'),
                    course_id
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error inserting book: {e}")
            return False
    
    def get_courses(self) -> List[Dict[str, Any]]:
        """Get all courses from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM courses')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_chapters(self, course_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get chapters, optionally filtered by course_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if course_id:
                cursor.execute('SELECT * FROM chapters WHERE course_id = ?', (course_id,))
            else:
                cursor.execute('SELECT * FROM chapters')
            return [dict(row) for row in cursor.fetchall()]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()