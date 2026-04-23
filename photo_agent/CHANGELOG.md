# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Environment variable support for all configuration parameters
- Security configuration (MAX_FILE_SIZE_MB, MAX_URL_LENGTH, path sanitization)
- Performance configuration (ENABLE_GPU, BATCH_SIZE, NUM_WORKERS, MEMORY_LIMIT_MB)
- URL validation with scheme and length checks
- File size validation for downloads
- Filename sanitization to prevent path traversal attacks
- Retry logic with exponential backoff for network requests
- Model caching singleton pattern for AI models
- GPU acceleration support with configurable enable/disable
- Comprehensive test suite for processor, downloader, and config modules
- GitHub Actions CI/CD workflow
- Pre-commit hooks configuration (Black, Flake8, isort, mypy)

### Changed
- Refactored configuration module to support environment variables
- Improved error handling and logging throughout the codebase
- Enhanced security measures for file downloads and extraction
- Updated AI Brain to use cached model loading

### Fixed
- Path traversal vulnerability in archive extraction
- Missing input validation for URLs and file sizes
- Redundant AI model loading across multiple Processor instances

## [1.0.7] - 2024-01-XX

### Added
- Initial release of AI Photo Agent V107
- CLIP-based image context detection
- Knowledge base matching for product classification
- Geometric analysis for plate detection
- Background texture analysis
- Automatic shape classification
- Multi-format archive support (Yandex Disk, Google Drive, direct URLs)
- Batch processing capabilities
- Cyrillic filename encoding support

