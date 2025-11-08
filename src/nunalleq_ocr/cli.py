"""
Command-line interface for the Nunalleq OCR system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .detector import ArtifactDetector
from .renamer import ArtifactRenamer


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def cmd_detect(args):
    """Handle the 'detect' command."""
    detector = ArtifactDetector(
        tesseract_cmd=args.tesseract_cmd
    )

    image_path = Path(args.image)

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing: {image_path.name}")
    result = detector.detect(image_path)

    print("\nDetection Results:")
    print(f"  Site Number:     {result.site_number or 'Not found'}")
    print(f"  Artifact Number: {result.artifact_number or 'Not found'}")

    if result.is_valid:
        print(f"\nProposed filename: {result.get_filename(image_path.suffix.lstrip('.'))}")
    else:
        print("\n⚠ Warning: Could not detect both site and artifact numbers")

    if args.show_text:
        print(f"\nRaw OCR Text:\n{result.raw_text}")

    sys.exit(0 if result.is_valid else 1)


def cmd_rename(args):
    """Handle the 'rename' command."""
    detector = ArtifactDetector(tesseract_cmd=args.tesseract_cmd)
    renamer = ArtifactRenamer(
        detector=detector,
        dry_run=args.dry_run,
        backup=args.backup
    )

    # Single file mode
    if args.image:
        image_path = Path(args.image)
        success, message = renamer.rename_file(
            image_path,
            output_dir=Path(args.output) if args.output else None,
            overwrite=args.overwrite
        )

        print(message)
        sys.exit(0 if success else 1)

    # Batch mode
    elif args.directory:
        input_dir = Path(args.directory)

        if not input_dir.exists():
            print(f"Error: Directory not found: {input_dir}", file=sys.stderr)
            sys.exit(1)

        results = renamer.rename_batch(
            input_dir,
            output_dir=Path(args.output) if args.output else None,
            pattern=args.pattern,
            overwrite=args.overwrite
        )

        # Print results
        print(f"\nProcessed {results['total']} files:")
        print(f"  ✓ Success: {results['success']}")
        print(f"  ✗ Failed:  {results['failed']}")

        # Show details if verbose or if there were failures
        if args.verbose or results['failed'] > 0:
            print("\nDetails:")
            for item in results['results']:
                status = "✓" if item['success'] else "✗"
                print(f"  {status} {item['message']}")

        sys.exit(0 if results['failed'] == 0 else 1)


def cmd_preview(args):
    """Handle the 'preview' command."""
    detector = ArtifactDetector(tesseract_cmd=args.tesseract_cmd)
    renamer = ArtifactRenamer(detector=detector)

    input_dir = Path(args.directory)

    if not input_dir.exists():
        print(f"Error: Directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    previews = renamer.preview_batch(input_dir, pattern=args.pattern)

    if not previews:
        print(f"No files matching '{args.pattern}' found in {input_dir}")
        sys.exit(0)

    print(f"\nPreview of {len(previews)} files in {input_dir}:\n")
    print(f"{'Original':<30} {'New Name':<30} {'Site':<12} {'Artifact':<10} {'Status'}")
    print("-" * 100)

    for preview in previews:
        print(
            f"{preview['original']:<30} "
            f"{preview['new_name']:<30} "
            f"{preview['site']:<12} "
            f"{preview['artifact']:<10} "
            f"{preview['status']}"
        )

    success_count = sum(1 for p in previews if "✓" in p['status'])
    print(f"\n{success_count}/{len(previews)} files ready for renaming")

    sys.exit(0)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Nunalleq OCR - Artifact Photo Organization System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect numbers from a single image
  nunalleq-ocr detect image.jpg

  # Preview what would happen when renaming all JPGs in a directory
  nunalleq-ocr preview images/

  # Rename all JPG files in a directory (dry run)
  nunalleq-ocr rename images/ --dry-run

  # Rename all JPG files for real
  nunalleq-ocr rename images/

  # Rename with output to a different directory
  nunalleq-ocr rename images/ --output renamed/

For more information, visit: https://github.com/yourusername/nunalleq-ocr
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--tesseract-cmd',
        type=str,
        help='Path to tesseract executable (auto-detected if not specified)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Detect command
    detect_parser = subparsers.add_parser(
        'detect',
        help='Detect site and artifact numbers from a single image'
    )
    detect_parser.add_argument('image', type=str, help='Path to image file')
    detect_parser.add_argument(
        '--show-text',
        action='store_true',
        help='Show raw OCR text'
    )
    detect_parser.set_defaults(func=cmd_detect)

    # Rename command
    rename_parser = subparsers.add_parser(
        'rename',
        help='Rename artifact photos based on OCR detection'
    )

    rename_group = rename_parser.add_mutually_exclusive_group(required=True)
    rename_group.add_argument(
        'image',
        nargs='?',
        type=str,
        help='Single image file to rename'
    )
    rename_group.add_argument(
        '-d', '--directory',
        type=str,
        help='Directory containing images to rename'
    )

    rename_parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output directory for renamed files (default: rename in place)'
    )
    rename_parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*.jpg',
        help='File pattern to match (default: *.jpg)'
    )
    rename_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be renamed without actually renaming'
    )
    rename_parser.add_argument(
        '--no-backup',
        dest='backup',
        action='store_false',
        help='Do not create backup of original files'
    )
    rename_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing files'
    )
    rename_parser.set_defaults(func=cmd_rename)

    # Preview command
    preview_parser = subparsers.add_parser(
        'preview',
        help='Preview detection results without renaming'
    )
    preview_parser.add_argument(
        'directory',
        type=str,
        help='Directory containing images'
    )
    preview_parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*.jpg',
        help='File pattern to match (default: *.jpg)'
    )
    preview_parser.set_defaults(func=cmd_preview)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
