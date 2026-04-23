#!/usr/bin/env python3
"""
AI Photo Agent V107 - Main Entry Point

Command-line interface for batch processing images from cloud storage links.
Supports Yandex Disk, Google Drive, and direct URLs.
"""

import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from photo_agent import __version__
from photo_agent.src import (
    Config,
    Processor,
    NameGenerator,
    DownloadManager,
    setup_logging
)


def get_user_links() -> List[str]:
    """Interactively collect download links from user."""
    print("\n=== AI PHOTO AGENT V107 ===")
    print("Paste archive links (one per line, empty line to start):")
    
    links = []
    while True:
        try:
            link = input("Link: ").strip()
            if not link:
                break
            links.append(link)
        except EOFError:
            break
    
    return links


def collect_image_files(download_dir: str) -> Dict[str, List[str]]:
    """
    Walk download directory and group images by article number.
    
    Args:
        download_dir: Root directory containing downloaded files
        
    Returns:
        Dictionary mapping article numbers to lists of image paths
    """
    batches: Dict[str, List[str]] = defaultdict(list)
    
    for root, dirs, files in os.walk(download_dir):
        image_files = [
            f for f in files 
            if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))
        ]
        
        if not image_files:
            continue
        
        folder_name = os.path.basename(root)
        
        for img_file in image_files:
            # Determine article number
            if root != download_dir and re.search(r'\d', folder_name):
                article = NameGenerator.extract_article(folder_name)
            else:
                article = NameGenerator.extract_article(img_file)
            
            batches[article].append(os.path.join(root, img_file))
    
    return batches


def process_batch(
    article: str,
    image_paths: List[str],
    processor: Processor,
    output_dir: str
) -> None:
    """
    Process a batch of images for a single article.
    
    Args:
        article: Article number/identifier
        image_paths: List of paths to image files
        processor: Processor instance
        output_dir: Directory for saving results
    """
    logger = __import__('logging').getLogger("PhotoAgent")
    logger.info(f"--- Processing Batch: {article} ---")
    
    results = []
    
    # Process each image
    for path in image_paths:
        processed_img, context_type = processor.process(path)
        if processed_img:
            results.append({'img': processed_img, 'type': context_type})
    
    # Sort by context type priority
    type_order = {'PLATE': '_1', 'PRODUCT': '_2', 'LIFESTYLE': '_3'}
    for item in results:
        item['pref'] = type_order.get(item['type'], '_0')
    
    sorted_results = sorted(results, key=lambda x: x['pref'])
    
    # Save with proper naming
    counts = {'_1': 0, '_2': 0, '_3': 0, '_0': 0}
    for item in sorted_results:
        prefix = item['pref']
        counts[prefix] += 1
        suffix = "" if counts[prefix] == 1 else f"({counts[prefix] - 1})"
        
        output_name = f"{article}{prefix}{suffix}.png"
        output_path = os.path.join(output_dir, output_name)
        
        item['img'].save(output_path)
        logger.info(f"  > Saved: {output_name} [{item['type']}]")


def cleanup_temp_dirs() -> None:
    """Remove temporary download directory."""
    try:
        if os.path.exists(Config.PATHS.DOWNLOAD_DIR):
            shutil.rmtree(Config.PATHS.DOWNLOAD_DIR)
    except OSError:
        pass


def main() -> int:
    """Main entry point."""
    # Setup logging
    logger = setup_logging()
    
    # Get links from user
    links = get_user_links()
    if not links:
        print("No links provided. Exiting.")
        return 0
    
    # Initialize processor
    processor = Processor(
        knowledge_base_dir=Config.PATHS.KNOWLEDGE_BASE_DIR
    )
    
    # Ensure output directory exists
    os.makedirs(Config.PATHS.OUTPUT_DIR, exist_ok=True)
    
    # Process each link
    for url in links:
        # Clean up previous download
        if os.path.exists(Config.PATHS.DOWNLOAD_DIR):
            shutil.rmtree(Config.PATHS.DOWNLOAD_DIR)
        
        # Download and extract
        if not DownloadManager.download_and_extract(
            url, Config.PATHS.DOWNLOAD_DIR
        ):
            logger.error(f"Failed to download: {url}")
            continue
        
        # Collect and group images
        batches = collect_image_files(Config.PATHS.DOWNLOAD_DIR)
        
        # Process each batch
        for article, paths in batches.items():
            process_batch(
                article, paths, processor, Config.PATHS.OUTPUT_DIR
            )
    
    # Cleanup
    cleanup_temp_dirs()
    
    print("\n✓ Processing complete!")
    print(f"Results saved to: {os.path.abspath(Config.PATHS.OUTPUT_DIR)}")
    
    # Wait for user acknowledgment
    try:
        input("\nPress Enter to Exit...")
    except EOFError:
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
