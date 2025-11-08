# Nunalleq OCR

An OCR-based artifact photo organization system for the Nunalleq museum. This tool automatically detects site numbers (e.g., GDN-248) and artifact numbers from archaeological artifact photos, then renames files following a consistent naming convention.

## Features

- **Robust OCR Detection**: Uses Tesseract OCR with advanced image preprocessing to extract text from artifact photos
- **Flexible Pattern Matching**: Handles various text layouts and spacing variations
- **Batch Processing**: Process entire directories of artifact photos at once
- **Safe Operations**: Includes dry-run mode and automatic backups
- **CLI Interface**: Easy-to-use command-line tools
- **Python API**: Import and use in your own scripts

## Installation

### Prerequisites

1. **Python 3.9 or higher**

2. **Tesseract OCR** - Install for your platform:

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   ```

   **macOS:**
   ```bash
   brew install tesseract
   ```

   **Windows:**
   Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install nunalleq-ocr

#### From source (for development):

```bash
# Clone or navigate to the project directory
cd ocr_nunalleq

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

#### For production use:

```bash
pip install nunalleq-ocr
```

## Quick Start

### 1. Detect numbers from a single image

```bash
nunalleq-ocr detect images/DSC_3288.jpg
```

Output:
```
Analyzing: DSC_3288.jpg

Detection Results:
  Site Number:     GDN-248
  Artifact Number: 76656

Proposed filename: gdn248_76656.jpg
```

### 2. Preview what would happen when renaming files

```bash
nunalleq-ocr preview images/
```

Output:
```
Preview of 2 files in images/:

Original                       New Name                       Site         Artifact   Status
----------------------------------------------------------------------------------------------------
DSC_2188.jpg                   gdn248_77238.jpg               GDN-248      77238      ✓ Ready
DSC_3288.jpg                   gdn248_76656.jpg               GDN-248      76656      ✓ Ready

2/2 files ready for renaming
```

### 3. Rename files (dry run first)

```bash
# See what would happen without actually renaming
nunalleq-ocr rename images/ --dry-run

# Actually rename the files
nunalleq-ocr rename images/
```

### 4. Rename with output to a different directory

```bash
nunalleq-ocr rename images/ --output renamed_photos/
```

## Usage

### Command-Line Interface

The `nunalleq-ocr` command provides three main subcommands:

#### `detect` - Analyze a single image

```bash
nunalleq-ocr detect <image_path> [options]

Options:
  --show-text    Show the raw OCR text extracted from the image
  --verbose      Enable verbose logging
```

#### `preview` - Preview renaming without making changes

```bash
nunalleq-ocr preview <directory> [options]

Options:
  -p, --pattern PATTERN    File pattern to match (default: *.jpg)
  --verbose                Enable verbose logging
```

#### `rename` - Rename files based on OCR detection

```bash
# Rename a single file
nunalleq-ocr rename <image_path> [options]

# Rename all files in a directory
nunalleq-ocr rename -d <directory> [options]

Options:
  -d, --directory DIR      Directory containing images
  -o, --output DIR         Output directory (default: rename in place)
  -p, --pattern PATTERN    File pattern to match (default: *.jpg)
  --dry-run                Show what would happen without actually renaming
  --no-backup              Don't create backup copies
  --overwrite              Overwrite existing files
  --verbose                Enable verbose logging
```

### Python API

You can also use the package programmatically:

```python
from pathlib import Path
from nunalleq_ocr import ArtifactDetector, ArtifactRenamer

# Detect numbers from a single image
detector = ArtifactDetector()
result = detector.detect(Path("images/DSC_3288.jpg"))

print(f"Site: {result.site_number}")
print(f"Artifact: {result.artifact_number}")
print(f"New filename: {result.get_filename('jpg')}")

# Rename files
renamer = ArtifactRenamer(detector=detector)
success, message = renamer.rename_file(
    Path("images/DSC_3288.jpg"),
    output_dir=Path("renamed/")
)
print(message)

# Batch processing
results = renamer.rename_batch(
    Path("images/"),
    pattern="*.jpg"
)
print(f"Renamed {results['success']} files")
```

## Output Format

Files are renamed using the following convention:

```
{site_number}_{artifact_number}.{extension}
```

Examples:
- `DSC_3288.jpg` → `gdn248_76656.jpg`
- `DSC_2188.jpg` → `gdn248_77238.jpg`

The site number is converted to lowercase and hyphens are removed.

## Configuration

### Custom Tesseract Path

If Tesseract is not in your system PATH:

```bash
nunalleq-ocr detect image.jpg --tesseract-cmd /path/to/tesseract
```

Or in Python:

```python
detector = ArtifactDetector(tesseract_cmd="/path/to/tesseract")
```

### Custom Site Number Pattern

The default pattern matches `GDN-XXX` format. To use a different pattern:

```python
detector = ArtifactDetector(site_pattern=r"ABC[-\s]?\d+")
```

## Troubleshooting

### No text detected

If OCR is not detecting text:

1. Check that Tesseract is properly installed:
   ```bash
   tesseract --version
   ```

2. Ensure image quality is good (sufficient resolution, clear text)

3. Try with `--verbose` flag to see debug information:
   ```bash
   nunalleq-ocr detect image.jpg --verbose --show-text
   ```

### Detection accuracy issues

The system is optimized for:
- White or light backgrounds
- Consistent typeface
- Site numbers in format: GDN-248
- Artifact numbers: 5-7 digits (may have spaces)

If detection is failing:
- Ensure proper lighting and focus in photos
- Check that labels are clearly visible
- Verify the format matches expected patterns

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=nunalleq_ocr --cov-report=html
```

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

## Project Structure

```
ocr_nunalleq/
├── src/
│   └── nunalleq_ocr/
│       ├── __init__.py       # Package initialization
│       ├── detector.py       # OCR detection logic
│       ├── renamer.py        # File renaming logic
│       └── cli.py            # Command-line interface
├── tests/                    # Unit tests
├── images/                   # Sample images
├── examples/                 # Example configurations
├── pyproject.toml            # Package configuration
├── README.md                 # This file
└── LICENSE                   # License information
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Developed for the Nunalleq archaeological project to help organize and catalog artifact photographs.

## Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.
