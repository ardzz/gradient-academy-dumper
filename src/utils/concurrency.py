"""Concurrency utilities for the scraper."""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, TypeVar, Dict, Optional, Iterable, Union

from rich.progress import Progress, TaskID

from ..config import MAX_WORKERS
from .console import console

T = TypeVar('T')

def run_with_concurrency(func: Callable[[Any], T], 
                        items: List[Any], 
                        max_workers: int = MAX_WORKERS,
                        show_progress: bool = True,
                        description: str = "Processing items") -> List[T]:
    """Run a function concurrently with a list of items.

    Args:
        func: The function to run concurrently
        items: List of items to process
        max_workers: Maximum number of worker threads
        show_progress: Whether to show a progress bar
        description: Description for the progress bar

    Returns:
        List of results from the function calls
    """
    results = []
    total_items = len(items)

    if not items:
        return results

    if show_progress:
        with Progress() as progress:
            task = progress.add_task(f"[cyan]{description}...", total=total_items)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(func, item): item for item in items}

                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        console.print(f"[red]Error processing {item}: {e}[/]")
                    finally:
                        progress.update(task, advance=1)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(func, item) for item in items]
            for future in futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    console.print(f"[red]Error in concurrent execution: {e}[/]")

    return results

def run_with_concurrency_dict(func: Callable[[Any], T],
                             items_dict: Dict[Any, Any],
                             key_arg: bool = False,
                             max_workers: int = MAX_WORKERS,
                             show_progress: bool = True,
                             description: str = "Processing items") -> Dict[Any, T]:
    """Run a function concurrently with a dictionary of items.

    Args:
        func: The function to run concurrently
        items_dict: Dictionary where keys are identifiers and values are items to process
        key_arg: If True, passes both key and value to func(key, value), otherwise just passes value
        max_workers: Maximum number of worker threads
        show_progress: Whether to show a progress bar
        description: Description for the progress bar

    Returns:
        Dictionary mapping original keys to results
    """
    results = {}
    total_items = len(items_dict)

    if not items_dict:
        return results

    if show_progress:
        with Progress() as progress:
            task = progress.add_task(f"[cyan]{description}...", total=total_items)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for key, value in items_dict.items():
                    if key_arg:
                        futures[executor.submit(func, key, value)] = key
                    else:
                        futures[executor.submit(func, value)] = key

                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        result = future.result()
                        results[key] = result
                    except Exception as e:
                        console.print(f"[red]Error processing {key}: {e}[/]")
                    finally:
                        progress.update(task, advance=1)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for key, value in items_dict.items():
                if key_arg:
                    futures[executor.submit(func, key, value)] = key
                else:
                    futures[executor.submit(func, value)] = key

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    console.print(f"[red]Error processing {key}: {e}[/]")

    return results

async def run_async_with_concurrency(func: Callable[[Any], Any], 
                                   items: List[Any], 
                                   max_concurrency: int = MAX_WORKERS) -> List[Any]:
    """Run an async function concurrently with a list of items."""
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def limited_func(item):
        async with semaphore:
            return await func(item)
    
    return await asyncio.gather(*[limited_func(item) for item in items], 
                              return_exceptions=True)