# AI Photo Agent V107

Professional image processing pipeline for e-commerce photography using AI-powered context detection and geometric analysis.

## Features

- **AI Context Detection**: Automatically classifies images as PRODUCT, PLATE, or LIFESTYLE using CLIP model
- **Knowledge Base Matching**: Learn from reference images for consistent results
- **Ellipse Reconstruction**: Intelligently reconstructs full plate boundaries from partial detections
- **Smart Composition**: Automatic scaling and centering based on object type and shape
- **Multi-Source Downloads**: Supports Yandex Disk, Google Drive, and direct URLs
- **Batch Processing**: Process multiple archives with automatic article grouping

## Installation

### From Source

```bash
cd photo_agent
pip install -e .
```

### With Development Dependencies

```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- PyTorch
- Transformers (CLIP)
- OpenCV
- Pillow
- rembg
- requests
- gdown (optional, for Google Drive)

## Usage

### Command Line

Run the interactive CLI:

```bash
photo-agent
```

Or run directly:

```bash
python -m photo_agent.src.cli
```

### As a Library

```python
from photo_agent.src import Processor, setup_logging

# Initialize
logger = setup_logging()
processor = Processor(knowledge_base_dir="knowledge_base")

# Process single image
processed_img, context_type = processor.process("input.jpg")
if processed_img:
    processed_img.save("output.png")
    print(f"Context: {context_type}")
```

## Project Structure

```
photo_agent/
├── __init__.py              # Package metadata
├── pyproject.toml           # Build configuration
├── README.md                # This file
├── requirements.txt         # Dependencies
├── src/
│   ├── __init__.py          # Source package init
│   ├── cli.py               # Command-line interface
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration classes
│   │   ├── geometry.py      # Geometric analysis
│   │   └── processor.py     # Main processing pipeline
│   ├── ai/
│   │   ├── __init__.py
│   │   └── brain.py         # AI model wrapper
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging setup
│       ├── namer.py         # Name generation
│       └── downloader.py    # Download manager
├── tests/                   # Test suite
└── knowledge_base/          # Reference images
    ├── PLATE/
    ├── PRODUCT/
    └── LIFESTYLE/
```

## Configuration

All configuration is centralized in `src/core/config.py`. Key parameters:

### Canvas Settings
- `CANVAS_W`: Output width (default: 1280)
- `CANVAS_H`: Output height (default: 840)
- `PRODUCT_BG_COLOR`: Background color (default: #FAFAFA)

### AI Thresholds
- `AI_CONFIDENCE_THRESHOLD`: Minimum confidence for AI predictions (default: 0.80)
- `SIMILARITY_THRESHOLD`: Knowledge base match threshold (default: 0.92)

### Geometry
- `PLATE_SOLIDITY_MIN`: Minimum solidity for plate detection (default: 0.93)
- `PLATE_CIRCULARITY_MIN`: Minimum circularity for plate detection (default: 0.74)

## Adding Reference Images

To improve classification accuracy, add reference images to the knowledge base:

```bash
knowledge_base/
├── PLATE/          # Add plate examples here
├── PRODUCT/        # Add product examples here
└── LIFESTYLE/      # Add lifestyle examples here
```

The agent will automatically load these on startup.

## Output Naming

Files are named based on detected article number and context:

- `{article}_1.png` - Plate images
- `{article}_2.png` - Product images  
- `{article}_3.png` - Lifestyle images
- `{article}_2(1).png` - Additional images of same type

## License

MIT License
