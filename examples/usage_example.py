"""
Example usage of the Nunalleq OCR package.

This script demonstrates how to use the package programmatically
for detecting artifact numbers and renaming files.
"""

from pathlib import Path
from nunalleq_ocr import ArtifactDetector, ArtifactRenamer

def example_single_image_detection():
    """Example: Detect site and artifact numbers from a single image."""
    print("=" * 60)
    print("Example 1: Single Image Detection")
    print("=" * 60)

    detector = ArtifactDetector()

    # Path to sample image
    image_path = Path("images/DSC_3288.jpg")

    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return

    # Detect numbers
    result = detector.detect(image_path)

    print(f"\nAnalyzing: {image_path.name}")
    print(f"Site Number:     {result.site_number or 'Not found'}")
    print(f"Artifact Number: {result.artifact_number or 'Not found'}")

    if result.is_valid:
        print(f"Proposed name:   {result.get_filename('jpg')}")
    else:
        print("Warning: Could not detect both numbers")

    print()


def example_batch_detection():
    """Example: Detect numbers from multiple images."""
    print("=" * 60)
    print("Example 2: Batch Detection")
    print("=" * 60)

    detector = ArtifactDetector()
    image_dir = Path("images")

    if not image_dir.exists():
        print(f"Directory not found: {image_dir}")
        return

    # Get all JPG files
    image_files = list(image_dir.glob("*.jpg"))

    if not image_files:
        print(f"No JPG files found in {image_dir}")
        return

    print(f"\nProcessing {len(image_files)} images...\n")

    # Process each image
    for img_path in image_files:
        result = detector.detect(img_path)

        status = "✓" if result.is_valid else "✗"
        print(f"{status} {img_path.name:30} -> {result.get_filename('jpg') or 'N/A'}")

    print()


def example_preview_renaming():
    """Example: Preview what would happen when renaming files."""
    print("=" * 60)
    print("Example 3: Preview Renaming")
    print("=" * 60)

    detector = ArtifactDetector()
    renamer = ArtifactRenamer(detector=detector)

    image_dir = Path("images")

    if not image_dir.exists():
        print(f"Directory not found: {image_dir}")
        return

    # Get preview
    previews = renamer.preview_batch(image_dir, pattern="*.jpg")

    if not previews:
        print("No images found")
        return

    print(f"\nPreview of renaming {len(previews)} files:\n")

    for preview in previews:
        print(f"  {preview['original']:30} -> {preview['new_name']:30} [{preview['status']}]")

    print()


def example_rename_with_output_dir():
    """Example: Rename files with output to a different directory."""
    print("=" * 60)
    print("Example 4: Rename with Output Directory (Dry Run)")
    print("=" * 60)

    detector = ArtifactDetector()
    renamer = ArtifactRenamer(detector=detector, dry_run=True)

    image_dir = Path("images")
    output_dir = Path("renamed_artifacts")

    if not image_dir.exists():
        print(f"Directory not found: {image_dir}")
        return

    # Rename files (dry run)
    results = renamer.rename_batch(
        image_dir,
        output_dir=output_dir,
        pattern="*.jpg"
    )

    print(f"\nProcessed {results['total']} files:")
    print(f"  Success: {results['success']}")
    print(f"  Failed:  {results['failed']}")

    print("\nDetails:")
    for item in results['results']:
        status = "✓" if item['success'] else "✗"
        print(f"  {status} {item['message']}")

    print()


def example_custom_configuration():
    """Example: Use custom configuration for different site patterns."""
    print("=" * 60)
    print("Example 5: Custom Site Pattern")
    print("=" * 60)

    # Create detector with custom site pattern
    # This example shows how to adapt to different site naming conventions
    detector = ArtifactDetector(
        site_pattern=r"[A-Z]{3}[-\s]?\d+"  # Matches any 3-letter code followed by numbers
    )

    print("\nCustom detector configured for pattern: [A-Z]{3}[-]?\\d+")
    print("This will match patterns like: ABC-123, XYZ-456, GDN-248, etc.")
    print()


if __name__ == "__main__":
    print("\nNunalleq OCR - Usage Examples")
    print("=" * 60)
    print()

    # Run all examples
    example_single_image_detection()
    example_batch_detection()
    example_preview_renaming()
    example_rename_with_output_dir()
    example_custom_configuration()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nFor actual renaming, set dry_run=False in ArtifactRenamer")
    print("or use the command-line tool: nunalleq-ocr rename images/")
    print()
