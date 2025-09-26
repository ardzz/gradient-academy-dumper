"""API client for Gradient Academy."""
import time
from typing import Dict, List, Optional, Any, Union

import httpx
from pydantic import ValidationError

from ..config import API_BASE_URL, API_TOKEN
from ..utils.console import console
from .models import Course, Chapter, Subchapter, SubchapterDetail

class GradientClient:
    """Client for interacting with Gradient Academy API."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the client with authentication token."""
        self.token = token or API_TOKEN
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Token {self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Origin": "https://gradient.academy",
            "Referer": "https://gradient.academy/",
        }
        self.last_request_time = 0
        self._client = httpx.Client(timeout=30.0)
    
    def _rate_limit(self):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 0.5:  # Minimum 0.5s between requests
            time.sleep(0.5 - time_since_last)
        self.last_request_time = time.time()
    
    def request(self, method: str, path: str, **kwargs) -> dict:
        """Make an HTTP request to the API."""
        self._rate_limit()
        url = f"{self.base_url}{path}"
        kwargs["headers"] = {**self.headers, **(kwargs.get("headers", {}))}
        
        try:
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            console.print(f"[bold red]Error {e.response.status_code}[/] for {url}")
            console.print(f"Response: {e.response.text}")
            raise
        except httpx.HTTPError as e:
            console.print(f"[bold red]HTTP Error:[/] {e}")
            raise
    
    def get_courses(self, limit: int = 50) -> List[Course]:
        """Get list of available courses."""
        data = self.request("GET", f"/courses/v2/private/?limit={limit}")
        try:
            return [Course.model_validate(course) for course in data.get("data", [])]
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/] {e}")
            return []
    
    def get_course_content(self, course_slug: str) -> Dict[str, List[Union[Chapter, Any]]]:
        """Get content (chapters and books) for a specific course."""
        data = self.request("GET", f"/courses/{course_slug}/content/")
        result = {"chapters": [], "books": []}
        
        try:
            if "chapters" in data:
                result["chapters"] = [Chapter.model_validate(chapter) for chapter in data.get("chapters", [])]
            if "books" in data:
                result["books"] = data.get("books", [])
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/] {e}")
        
        return result
    
    def get_subchapters(self, chapter_id: str) -> List[Subchapter]:
        """Get subchapters for a specific chapter."""
        data = self.request("GET", f"/courses/{chapter_id}/subchapter/")
        try:
            return [Subchapter.model_validate(subchapter) for subchapter in data.get("subchapters", [])]
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/] {e}")
            return []
    
    def get_subchapter_detail(self, course_slug: str, subchapter_slug: str) -> Optional[SubchapterDetail]:
        """Get detailed information about a specific subchapter."""
        try:
            data = self.request(
                "GET", 
                f"/courses/v2/private/{course_slug}/subchapter/{subchapter_slug}/"
            )
            return SubchapterDetail.model_validate(data)
        except (ValidationError, httpx.HTTPError) as e:
            console.print(f"[bold red]Error getting subchapter detail:[/] {e}")
            return None
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()