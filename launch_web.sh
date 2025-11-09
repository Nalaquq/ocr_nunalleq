#!/bin/bash
# macOS/Linux launcher for Nunalleq OCR Web Interface
# Run this file to start the web application

echo "======================================================"
echo "  Nunalleq Artifact Photo Organizer - Web Interface"
echo "======================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Please install Python 3.9 or higher:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if nunalleq-ocr is installed
if ! python3 -c "import nunalleq_ocr" 2>/dev/null; then
    echo "Installing nunalleq-ocr with web interface..."
    python3 -m pip install -e ".[gui]"
    if [ $? -ne 0 ]; then
        echo "Installation failed. Please check the error messages above."
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    # Check if Flask is installed
    if ! python3 -c "import flask" 2>/dev/null; then
        echo "Installing web interface dependencies..."
        python3 -m pip install -e ".[gui]"
    fi
fi

# Launch the web interface
echo ""
echo "Starting web interface..."
echo "Your web browser will open automatically."
echo ""
echo "Press Ctrl+C to stop the server when you're done."
echo ""

python3 -m nunalleq_ocr.webapp.app
