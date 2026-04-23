"""
Download manager for remote image archives.

Supports multiple cloud storage providers including Yandex Disk,
Google Drive, and direct URLs.

Implements retry logic with exponential backoff and URL validation
for improved reliability and security.
"""

import os
import re
import shutil
import zipfile
import logging
from typing import Optional
from urllib.parse import urlencode, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False

from photo_agent.src.core.config import Config


logger = logging.getLogger(__name__)


class DownloadManager:
    """
    Manager for downloading and extracting image archives from various sources.
    
    Supports:
    - Direct URLs
    - Yandex Disk (disk.yandex.ru, yadi.sk)
    - Google Drive (drive.google.com)
    
    Features:
    - Retry logic with exponential backoff
    - URL validation and sanitization
    - File size limits
    - Secure filename handling
    """
    
    # Maximum number of retry attempts
    MAX_RETRIES = 3
    # Base delay for exponential backoff (seconds)
    BASE_DELAY = 1.0
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format and security constraints.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and safe, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        # Check URL length
        if len(url) > Config.SECURITY.MAX_URL_LENGTH:
            logger.error(f"URL exceeds maximum length of {Config.SECURITY.MAX_URL_LENGTH}")
            return False
        
        try:
            parsed = urlparse(url)
            
            # Must have http or https scheme
            if parsed.scheme not in ('http', 'https'):
                logger.error(f"Invalid URL scheme: {parsed.scheme}")
                return False
            
            # Must have a netloc (domain)
            if not parsed.netloc:
                logger.error("URL missing domain")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False
    
    @staticmethod
    def validate_file_size(file_path: str) -> bool:
        """
        Validate that file size is within acceptable limits.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file size is acceptable, False otherwise
        """
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            max_size = Config.SECURITY.MAX_FILE_SIZE_MB
            
            if size_mb > max_size:
                logger.error(f"File size {size_mb:.2f}MB exceeds limit of {max_size}MB")
                return False
            
            return True
            
        except OSError as e:
            logger.error(f"Could not check file size: {e}")
            return False
    
    @staticmethod
    def _create_session() -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=DownloadManager.MAX_RETRIES,
            backoff_factor=DownloadManager.BASE_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
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
        # Validate URL
        if not DownloadManager.validate_url(url):
            logger.error("Invalid or unsafe URL provided")
            return False
        
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
            
            # Validate downloaded file size
            if not DownloadManager.validate_file_size(archive_path):
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
                return False
            
            # Extract the archive
            return DownloadManager._extract_archive(archive_path, dest)
            
        except Exception as e:
            logger.error(f"Download error: {e}", exc_info=True)
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
        
        try:
            session = DownloadManager._create_session()
            response = session.get(api, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('href')
            else:
                logger.error(f"Yandex API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Yandex download URL error: {e}")
            return None
    
    @staticmethod
    def _download_google_drive(url: str, archive_path: str, dest: str) -> bool:
        """Download from Google Drive using gdown."""
        if not GDOWN_AVAILABLE:
            logger.error("gdown not installed. Install with: pip install gdown")
            return False
        
        try:
            gdown.download(url, output=archive_path, quiet=False, fuzzy=True)
            
            # Validate file size
            if not DownloadManager.validate_file_size(archive_path):
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
                return False
            
            return DownloadManager._extract_archive(archive_path, dest)
        except Exception as e:
            logger.error(f"Google Drive download error: {e}")
            return False
    
    @staticmethod
    def _download_file(url: str, path: str, headers: dict) -> bool:
        """Download file from direct URL with retry support."""
        try:
            session = DownloadManager._create_session()
            
            with session.get(url, stream=True, headers=headers, timeout=60) as response:
                response.raise_for_status()
                
                with open(path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"File download error after retries: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            return False
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        if not Config.SECURITY.ENABLE_PATH_SANITIZATION:
            return filename
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        safe_name = (
            filename
            .replace('\t', ' ')
            .replace('\n', '')
            .replace('\r', '')
        )
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', safe_name).strip()
        
        # Remove leading dots to prevent hidden files
        while safe_name.startswith('.'):
            safe_name = safe_name[1:]
        
        # Limit filename length
        if len(safe_name) > 255:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:255-len(ext)] + ext
        
        return safe_name if safe_name else 'unnamed_file'
    
    @staticmethod
    def _extract_archive(archive_path: str, dest: str) -> bool:
        """
        Extract ZIP archive with encoding handling and security checks.
        
        Handles CP866 (Windows Cyrillic) encoded filenames and
        sanitizes problematic characters.
        
        Security features:
        - Path traversal prevention
        - Filename sanitization
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
                    safe_name = DownloadManager._sanitize_filename(member.filename)
                    
                    # Skip macOS metadata and system files
                    if "__MACOSX" in safe_name or safe_name.startswith('.'):
                        continue
                    
                    # Build target path securely
                    target = os.path.normpath(os.path.join(dest, safe_name))
                    
                    # Prevent path traversal
                    if not target.startswith(os.path.normpath(dest)):
                        logger.warning(f"Skipping file with path traversal attempt: {member.filename}")
                        continue
                    
                    if member.is_dir():
                        os.makedirs(target, exist_ok=True)
                    else:
                        # Create parent directories
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        
                        # Extract file
                        with zf.open(member) as source, open(target, 'wb') as target_file:
                            shutil.copyfileobj(source, target_file)
            
            return True
            
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid or corrupted ZIP file: {e}")
            return False
        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            return False
