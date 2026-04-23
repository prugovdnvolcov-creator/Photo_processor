"""
Download manager for remote image archives.

Supports multiple cloud storage providers including Yandex Disk,
Google Drive, and direct URLs.
"""

import os
import re
import shutil
import zipfile
from typing import Optional
from urllib.parse import urlencode

import requests

try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False

from photo_agent.src.core.config import Config


class DownloadManager:
    """
    Manager for downloading and extracting image archives from various sources.
    
    Supports:
    - Direct URLs
    - Yandex Disk (disk.yandex.ru, yadi.sk)
    - Google Drive (drive.google.com)
    """
    
    @staticmethod
    def download_and_extract(url: str, dest: str) -> bool:
        """
        Download archive from URL and extract contents.
        
        Args:
            url: Source URL for the archive
            dest: Destination directory for extracted files
            
        Returns:
            True if successful, False otherwise
        """
        os.makedirs(dest, exist_ok=True)
        archive_path = os.path.join(dest, "archive.zip")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        download_url: Optional[str] = None
        
        try:
            # Handle different URL types
            if "disk.yandex" in url or "yadi.sk" in url:
                download_url = DownloadManager._get_yandex_download_url(url, headers)
            elif "drive.google.com" in url:
                return DownloadManager._download_google_drive(url, archive_path, dest)
            else:
                download_url = url
            
            # Download the archive
            if download_url:
                if not DownloadManager._download_file(download_url, archive_path, headers):
                    return False
            
            # Extract the archive
            return DownloadManager._extract_archive(archive_path, dest)
            
        except Exception as e:
            import logging
            logging.getLogger("PhotoAgent").error(f"Download error: {e}")
            return False
        finally:
            # Clean up archive file
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
    
    @staticmethod
    def _get_yandex_download_url(url: str, headers: dict) -> Optional[str]:
        """Get direct download URL from Yandex Disk public link."""
        api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
        api += urlencode({'public_key': url})
        
        response = requests.get(api, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get('href')
        
        return None
    
    @staticmethod
    def _download_google_drive(url: str, archive_path: str, dest: str) -> bool:
        """Download from Google Drive using gdown."""
        if not GDOWN_AVAILABLE:
            import logging
            logging.getLogger("PhotoAgent").error(
                "gdown not installed. Install with: pip install gdown"
            )
            return False
        
        try:
            gdown.download(url, output=archive_path, quiet=False, fuzzy=True)
            return DownloadManager._extract_archive(archive_path, dest)
        except Exception as e:
            import logging
            logging.getLogger("PhotoAgent").error(f"Google Drive download error: {e}")
            return False
    
    @staticmethod
    def _download_file(url: str, path: str, headers: dict) -> bool:
        """Download file from direct URL."""
        try:
            with requests.get(url, stream=True, headers=headers, timeout=60) as response:
                response.raise_for_status()
                with open(path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
            return True
        except Exception as e:
            import logging
            logging.getLogger("PhotoAgent").error(f"File download error: {e}")
            return False
    
    @staticmethod
    def _extract_archive(archive_path: str, dest: str) -> bool:
        """
        Extract ZIP archive with encoding handling.
        
        Handles CP866 (Windows Cyrillic) encoded filenames and
        sanitizes problematic characters.
        """
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for member in zf.infolist():
                    # Try to decode Cyrillic filenames
                    try:
                        member.filename = member.filename.encode('cp437').decode('cp866')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        pass
                    
                    # Sanitize filename
                    safe_name = (
                        member.filename
                        .replace('\t', ' ')
                        .replace('\n', '')
                        .replace('\r', '')
                    )
                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name).strip()
                    
                    # Skip macOS metadata
                    if "__MACOSX" in safe_name:
                        continue
                    
                    target = os.path.join(dest, safe_name)
                    
                    if member.is_dir():
                        os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with zf.open(member) as source, open(target, 'wb') as target_file:
                            shutil.copyfileobj(source, target_file)
            
            return True
            
        except Exception as e:
            import logging
            logging.getLogger("PhotoAgent").error(f"Extraction error: {e}")
            return False
