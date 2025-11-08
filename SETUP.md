# Setup Guide for Nunalleq OCR

This guide will walk you through setting up the Nunalleq OCR system from scratch.

## Prerequisites

Before you begin, make sure you have the following installed:

1. **Python 3.9 or higher**
   - Check your version: `python --version` or `python3 --version`
   - Download from: https://www.python.org/downloads/

2. **Tesseract OCR**
   - This is the core OCR engine used by the package

### Installing Tesseract OCR

#### Ubuntu/Debian Linux
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

Verify installation:
```bash
tesseract --version
```

#### macOS
Using Homebrew:
```bash
brew install tesseract
```

Verify installation:
```bash
tesseract --version
```

#### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the prompts
3. Add Tesseract to your PATH or note the installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`)

Verify installation:
```cmd
tesseract --version
```

## Installation Steps

### Step 1: Navigate to the Project Directory

```bash
cd /path/to/ocr_nunalleq
```

### Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to isolate the project dependencies.

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 3: Install the Package

For development (recommended if you want to modify the code):
```bash
pip install -e ".[dev]"
```

For normal use:
```bash
pip install -e .
```

This will install:
- The `nunalleq-ocr` package
- All required dependencies (pytesseract, Pillow, opencv-python, numpy)
- Development tools (pytest, black, etc.) if using `[dev]`

### Step 4: Verify Installation

Test that the CLI is working:
```bash
nunalleq-ocr --version
```

You should see: `nunalleq-ocr 0.1.0`

### Step 5: Test with Sample Images

Try detecting numbers from the sample images:

```bash
nunalleq-ocr detect images/DSC_3288.jpg
```

You should see output like:
```
Analyzing: DSC_3288.jpg

Detection Results:
  Site Number:     GDN-248
  Artifact Number: 76656

Proposed filename: gdn248_76656.jpg
```

Preview renaming all images:
```bash
nunalleq-ocr preview images/
```

## Troubleshooting

### Issue: "tesseract: command not found"

**Solution**: Tesseract is not installed or not in your PATH.

- Verify Tesseract is installed: `tesseract --version`
- If on Windows, you may need to specify the path manually:
  ```bash
  nunalleq-ocr detect image.jpg --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```

### Issue: "No module named 'nunalleq_ocr'"

**Solution**: The package is not installed correctly.

- Make sure you're in the project directory
- Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
- Try reinstalling: `pip install -e .`

### Issue: Poor OCR accuracy

**Solution**: Ensure image quality is good.

- Images should have good lighting
- Text should be in focus and clearly visible
- White or light background works best
- Try with `--verbose` flag to see debug info

### Issue: Import errors with cv2

**Solution**: OpenCV installation issue.

```bash
pip uninstall opencv-python
pip install opencv-python
```

## Running Tests

After installation, you can run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=nunalleq_ocr

# Run specific test file
pytest tests/test_detector.py

# Run in verbose mode
pytest -v
```

## Development Setup

If you're planning to modify the code:

### Install development dependencies
```bash
pip install -e ".[dev]"
```

### Code formatting
```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/
```

### Type checking
```bash
mypy src/
```

### Running the linter
```bash
flake8 src/
```

## Next Steps

Now that you have the package installed:

1. Read the [README.md](README.md) for usage examples
2. Try the examples in `examples/usage_example.py`
3. Process your own artifact photos!

## Getting Help

- Check the [README.md](README.md) for common usage patterns
- Review the examples in the `examples/` directory
- Open an issue on GitHub if you encounter problems

## Uninstalling

To remove the package:

```bash
pip uninstall nunalleq-ocr
```

To remove the virtual environment:

```bash
# Deactivate first
deactivate

# Remove the directory
rm -rf venv/
```
