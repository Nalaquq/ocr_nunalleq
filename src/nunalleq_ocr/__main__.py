"""
Main entry point for running nunalleq_ocr as a module.

Usage:
    python -m nunalleq_ocr          # Run CLI
    python -m nunalleq_ocr.gui      # Run GUI
"""

from .cli import main

if __name__ == '__main__':
    main()
