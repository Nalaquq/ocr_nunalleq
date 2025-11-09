# Nunalleq Artifact Photo Organizer

Automatically rename artifact photos based on their labels using OCR (Optical Character Recognition).

Perfect for archaeologists and researchers who need to organize thousands of artifact photos without typing each name manually.

## Quick Start

### For Non-Technical Users (RECOMMENDED)

**Just double-click one file to get started:**

- **Windows:** Double-click `launch_web.bat`
- **Mac/Linux:** Double-click `launch_web.sh` (or run `./launch_web.sh` in terminal)

This will:
1. Open a web interface in your browser
2. Let you upload photos by clicking or dragging them
3. Process them automatically
4. Download a ZIP file with renamed photos

**That's it!** No typing paths, no terminal commands needed.

---

### For Technical Users

#### Installation

```bash
# Install the package
pip install -e .

# Verify installation
nunalleq-ocr --version
```

#### Quick Usage

```bash
# Launch web interface (easiest)
nunalleq-ocr web

# Or use command line:
# Preview what will happen (safe, no changes)
nunalleq-ocr preview photos/

# Process photos and save to new folder
nunalleq-ocr rename photos/ --output renamed/

# Process a single photo
nunalleq-ocr detect photo.jpg
```

---

## How It Works

1. **Upload photos** - Artifact photos with visible labels
2. **OCR Detection** - Automatically reads site number (e.g., "GDN-248") and artifact number (e.g., "105407")
3. **Smart Renaming** - Creates clean filenames: `GDN-248_105407.jpg`
4. **Download** - Get all renamed photos in a ZIP file

### What it reads

The tool looks for these patterns on artifact labels:
- **Site Number:** e.g., `GDN-248`, `GDN 248`
- **Artifact Number:** e.g., `105407`, `105-407`

### Example

**Before:** `DSC_3288.jpg`
**After:** `GDN-248_105407.jpg`

---

## Features

✅ **Safe**: Never modifies original photos
✅ **Smart**: Uses advanced OCR to read handwritten and printed labels
✅ **Fast**: Process hundreds of photos automatically
✅ **Easy**: Web interface requires no technical knowledge
✅ **Flexible**: Command-line tools for advanced users

---

## Usage Modes

### 1. Web Interface (Recommended)

**Launch:**
```bash
nunalleq-ocr web
```

**Or just double-click:** `launch_web.bat` (Windows) or `launch_web.sh` (Mac/Linux)

**Features:**
- Drag and drop photos
- Real-time progress bar
- Download results as ZIP
- No file paths to type
- Perfect for non-technical users

### 2. Command Line Interface

#### Preview (Safe - No Changes)
```bash
nunalleq-ocr preview photos/
```
Shows what will happen without making any changes.

#### Process Photos
```bash
# Save to new folder (RECOMMENDED)
nunalleq-ocr rename photos/ --output renamed/

# Process recursively (including subfolders)
nunalleq-ocr rename photos/ --output renamed/ --recursive

# Single file
nunalleq-ocr rename photo.jpg --output renamed/
```

#### Detect Only
```bash
# Just see what the tool detects
nunalleq-ocr detect photo.jpg

# Show raw OCR text
nunalleq-ocr detect photo.jpg --show-text
```

### 3. Python API

```python
from nunalleq_ocr import ArtifactDetector, ArtifactRenamer
from pathlib import Path

# Detect numbers from a single image
detector = ArtifactDetector()
result = detector.detect(Path("photo.jpg"))

print(f"Site: {result.site_number}")
print(f"Artifact: {result.artifact_number}")
print(f"New name: {result.get_filename('jpg')}")

# Batch process
renamer = ArtifactRenamer(detector=detector)
results = renamer.rename_batch(
    Path("photos/"),
    output_dir=Path("renamed/"),
    pattern="*.jpg"
)

print(f"Success: {results['success']}/{results['total']}")
```

See `examples/usage_example.py` for more examples.

---

## Installation

### Requirements

- **Python 3.8+**
- **Tesseract OCR** (free, open source)

### Step 1: Install Tesseract OCR

#### Windows
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer
3. Add to PATH or the tool will find it automatically

#### Mac
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Step 2: Install This Package

```bash
# Clone or download this repository
cd ocr_nunalleq

# Install
pip install -e .
```

### Verify Installation

```bash
nunalleq-ocr --version
```

---

## Safety Features

### Your Original Photos Are ALWAYS Safe

- ✅ **Web Interface**: Photos are uploaded temporarily, processed, then deleted. Originals remain on your computer.
- ✅ **Command Line with --output**: Copies photos to new folder, originals untouched.
- ✅ **Preview Mode**: Shows what will happen without making any changes.

### Working with External Drives

**Do This (SAFE):**
```bash
# Copy FROM external drive TO your computer
nunalleq-ocr rename /Volumes/BACKUP/photos/ --output ~/Desktop/renamed/
```

**Not This:**
```bash
# Don't rename directly on external drives (might disconnect)
nunalleq-ocr rename /Volumes/BACKUP/photos/
```

**Why:** External drives can disconnect during processing. Always copy to your computer first.

---

## Troubleshooting

### "Tesseract not found"
- **Windows:** Reinstall Tesseract and make sure to check "Add to PATH"
- **Mac/Linux:** Run `which tesseract` to verify installation

### "No numbers detected"
- Labels might be unclear or too small
- Try with a clearer photo
- Check if the photo actually has visible labels

### "Permission denied"
- Make sure you have write access to the output folder
- Don't try to modify files on read-only drives

### Web interface won't load
- Make sure port 5000 is not in use
- Try: `nunalleq-ocr web --port 8000`

---

## Command Reference

```bash
# Web interface
nunalleq-ocr web                    # Start on port 5000
nunalleq-ocr web --port 8000        # Use different port
nunalleq-ocr web --debug            # Debug mode

# Preview (safe, no changes)
nunalleq-ocr preview DIRECTORY

# Rename photos
nunalleq-ocr rename DIRECTORY --output OUTPUT_DIR
nunalleq-ocr rename PHOTO.jpg --output OUTPUT_DIR
nunalleq-ocr rename DIRECTORY --output OUTPUT_DIR --recursive

# Detect single photo
nunalleq-ocr detect PHOTO.jpg
nunalleq-ocr detect PHOTO.jpg --show-text

# Help
nunalleq-ocr --help
nunalleq-ocr rename --help
```

---

## Development

### Running Tests
```bash
pytest tests/
```

### Project Structure
```
ocr_nunalleq/
├── src/nunalleq_ocr/       # Main package
│   ├── detector.py         # OCR detection logic
│   ├── renamer.py          # File renaming logic
│   ├── cli.py              # Command-line interface
│   └── webapp/             # Web interface
│       ├── app.py          # Flask backend
│       ├── static/         # CSS, JavaScript
│       └── templates/      # HTML templates
├── tests/                  # Unit tests
├── examples/               # Usage examples
├── launch_web.bat          # Windows launcher
├── launch_web.sh           # Mac/Linux launcher
└── README.md              # This file
```

---

## Credits

Developed for the Nunalleq archaeological project.

**Technologies:**
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [pytesseract](https://github.com/madmaze/pytesseract) - Python wrapper for Tesseract
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pillow](https://python-pillow.org/) - Image processing

---

## License

MIT License - See LICENSE file for details.

---

## Support

**Found a bug?** Open an issue on GitHub.

**Need help?** Check the examples in `examples/usage_example.py` or run `nunalleq-ocr --help`.
