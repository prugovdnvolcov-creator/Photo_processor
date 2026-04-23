"""
Tests for downloader module.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from photo_agent.src.utils.downloader import DownloadManager
from photo_agent.src.core.config import Config


class TestURLValidation:
    """Test URL validation functionality."""
    
    def test_valid_http_url(self):
        """Test valid HTTP URL passes validation."""
        url = "http://example.com/file.zip"
        assert DownloadManager.validate_url(url) is True
    
    def test_valid_https_url(self):
        """Test valid HTTPS URL passes validation."""
        url = "https://example.com/file.zip"
        assert DownloadManager.validate_url(url) is True
    
    def test_invalid_scheme(self):
        """Test invalid scheme fails validation."""
        url = "ftp://example.com/file.zip"
        assert DownloadManager.validate_url(url) is False
    
    def test_no_domain(self):
        """Test URL without domain fails validation."""
        url = "http:///file.zip"
        assert DownloadManager.validate_url(url) is False
    
    def test_empty_url(self):
        """Test empty URL fails validation."""
        assert DownloadManager.validate_url("") is False
        assert DownloadManager.validate_url(None) is False
    
    def test_url_too_long(self):
        """Test URL exceeding max length fails validation."""
        long_url = "http://example.com/" + "a" * 3000
        assert DownloadManager.validate_url(long_url) is False
    
    def test_yandex_url(self):
        """Test Yandex Disk URL passes validation."""
        url = "https://disk.yandex.ru/d/abc123"
        assert DownloadManager.validate_url(url) is True
    
    def test_google_drive_url(self):
        """Test Google Drive URL passes validation."""
        url = "https://drive.google.com/file/d/abc123/view"
        assert DownloadManager.validate_url(url) is True


class TestFilesizeValidation:
    """Test file size validation functionality."""
    
    def test_file_within_limit(self):
        """Test file within size limit passes validation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write 1MB of data
            f.write(b'x' * (1024 * 1024))
            temp_path = f.name
        
        try:
            result = DownloadManager.validate_file_size(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file(self):
        """Test nonexistent file fails validation."""
        result = DownloadManager.validate_file_size("/nonexistent/file.zip")
        assert result is False


class TestFilenameSanitization:
    """Test filename sanitization functionality."""
    
    def test_normal_filename(self):
        """Test normal filename passes through unchanged."""
        filename = "image.jpg"
        result = DownloadManager._sanitize_filename(filename)
        assert result == "image.jpg"
    
    def test_path_traversal_prevention(self):
        """Test path traversal attempts are blocked."""
        filename = "../../../etc/passwd"
        result = DownloadManager._sanitize_filename(filename)
        assert ".." not in result
        assert result == "passwd"
    
    def test_dangerous_characters_removed(self):
        """Test dangerous characters are replaced."""
        filename = "file<>name?.txt"
        result = DownloadManager._sanitize_filename(filename)
        assert "<" not in result
        assert ">" not in result
        assert "?" not in result
    
    def test_hidden_files_blocked(self):
        """Test leading dots are removed."""
        filename = ".hidden_file"
        result = DownloadManager._sanitize_filename(filename)
        assert not result.startswith('.')
    
    def test_long_filename_truncated(self):
        """Test very long filenames are truncated."""
        long_name = "a" * 300 + ".jpg"
        result = DownloadManager._sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_empty_result_handling(self):
        """Test empty filename gets default name."""
        filename = "\x00\x01\x02"
        result = DownloadManager._sanitize_filename(filename)
        assert result == "unnamed_file"
