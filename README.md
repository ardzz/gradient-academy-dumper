# Gradient Academy Scraper

A modular, concurrent scraper for Gradient Academy's API that stores data in SQLite.

## Features

- Scrapes courses, chapters, subchapters, videos, and related data
- Stores everything in SQLite database
- Uses concurrency for faster scraping
- Rich console UI for better user experience
- Modular design for easy maintenance and extension

## Requirements

- Python 3.9+
- `uv` for package management
- Dependencies:
  - httpx
  - pydantic
  - rich

## Installation

1. Clone this repository
2. Install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt