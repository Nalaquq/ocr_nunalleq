"""
File renaming module for organizing artifact photos.
"""

import logging
import shutil
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from .detector import ArtifactDetector, DetectionResult


logger = logging.getLogger(__name__)


class RenameError(Exception):
    """Exception raised when file renaming fails."""
    pass


class ArtifactRenamer:
    """
    Handles renaming of artifact photos based on OCR detection.

    Renames files to follow the pattern: {site_number}_{artifact_number}.{ext}
    Example: gdn248_76656.jpg
    """

    def __init__(
        self,
        detector: Optional[ArtifactDetector] = None,
        dry_run: bool = False,
        backup: bool = True
    ):
        """
        Initialize the artifact renamer.

        Args:
            detector: ArtifactDetector instance (creates new one if None)
            dry_run: If True, only simulate renaming without actual changes
            backup: If True, create backup of original files
        """
        self.detector = detector or ArtifactDetector()
        self.dry_run = dry_run
        self.backup = backup

    def rename_file(
        self,
        image_path: Path,
        output_dir: Optional[Path] = None,
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Rename a single image file based on OCR detection.

        Args:
            image_path: Path to the image file
            output_dir: Directory for renamed file (None = same directory)
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (success: bool, message: str)
        """
        image_path = Path(image_path)

        if not image_path.exists():
            return False, f"File not found: {image_path}"

        # Detect site and artifact numbers
        result = self.detector.detect(image_path)

        if not result.is_valid:
            return False, (
                f"Could not detect both site and artifact numbers. "
                f"Site: {result.site_number}, Artifact: {result.artifact_number}"
            )

        # Generate new filename
        extension = image_path.suffix.lstrip('.')
        new_filename = result.get_filename(extension)

        if not new_filename:
            return False, "Failed to generate filename"

        # Determine output path
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            new_path = output_dir / new_filename
        else:
            new_path = image_path.parent / new_filename

        # Check if file already exists
        if new_path.exists() and not overwrite and new_path != image_path:
            return False, f"File already exists: {new_path.name} (use --overwrite to replace)"

        # Dry run mode - only report what would happen
        if self.dry_run:
            return True, f"[DRY RUN] Would rename: {image_path.name} -> {new_filename}"

        # Create backup if requested
        if self.backup and new_path != image_path:
            backup_dir = image_path.parent / "backup"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / image_path.name
            try:
                shutil.copy2(image_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")

        # Perform the rename
        try:
            if output_dir:
                # Copy to new location
                shutil.copy2(image_path, new_path)
                logger.info(f"Copied: {image_path.name} -> {new_path}")
            else:
                # Rename in place
                image_path.rename(new_path)
                logger.info(f"Renamed: {image_path.name} -> {new_filename}")

            return True, f"Renamed: {image_path.name} -> {new_filename}"

        except Exception as e:
            error_msg = f"Error renaming {image_path.name}: {e}"
            logger.error(error_msg)
            return False, error_msg

    def rename_batch(
        self,
        image_dir: Path,
        output_dir: Optional[Path] = None,
        pattern: str = "*.jpg",
        overwrite: bool = False,
        create_log: bool = True
    ) -> dict[str, dict]:
        """
        Rename multiple images in a directory.

        Args:
            image_dir: Directory containing images
            output_dir: Directory for renamed files (None = same directory)
            pattern: Glob pattern for matching files (default: *.jpg)
            overwrite: Whether to overwrite existing files
            create_log: Whether to create detailed log files (default: True)

        Returns:
            Dictionary with statistics and results:
            {
                'total': int,
                'success': int,
                'failed': int,
                'results': List[dict],  # List of individual results
                'log_file': Path  # Path to log file if created
            }
        """
        image_dir = Path(image_dir)

        if not image_dir.exists():
            raise ValueError(f"Directory not found: {image_dir}")

        # Find all matching image files
        image_files = sorted(image_dir.glob(pattern))

        if not image_files:
            logger.warning(f"No files matching '{pattern}' found in {image_dir}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'results': [],
                'log_file': None
            }

        results = []
        success_count = 0
        failed_count = 0
        detections = []  # For detailed logging

        logger.info(f"Processing {len(image_files)} files...")

        for img_path in image_files:
            # Detect first to get detailed info
            detection_result = self.detector.detect(img_path)

            success, message = self.rename_file(img_path, output_dir, overwrite)

            result_entry = {
                'original': img_path.name,
                'success': success,
                'message': message,
                'site_number': detection_result.site_number,
                'artifact_number': detection_result.artifact_number,
                'confidence': detection_result.confidence,
                'new_name': detection_result.get_filename(img_path.suffix.lstrip('.')) if detection_result.is_valid else None
            }

            results.append(result_entry)
            detections.append(result_entry)

            if success:
                success_count += 1
            else:
                failed_count += 1

        # Create log files
        log_file = None
        if create_log:
            log_file = self._create_log_files(image_dir, output_dir, detections)

        return {
            'total': len(image_files),
            'success': success_count,
            'failed': failed_count,
            'results': results,
            'log_file': log_file
        }

    def _create_log_files(
        self,
        image_dir: Path,
        output_dir: Optional[Path],
        detections: List[Dict]
    ) -> Path:
        """
        Create detailed log files for the batch operation.

        Creates both a CSV and a JSON log file with all detection details.

        Args:
            image_dir: Source directory
            output_dir: Output directory (if any)
            detections: List of detection results

        Returns:
            Path to the CSV log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = output_dir if output_dir else image_dir
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # CSV log
        csv_path = log_dir / f"nunalleq_ocr_log_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'original', 'new_name', 'site_number', 'artifact_number',
                'confidence', 'success', 'message'
            ])
            writer.writeheader()
            writer.writerows(detections)

        # JSON log (more detailed)
        json_path = log_dir / f"nunalleq_ocr_log_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'source_directory': str(image_dir),
                'output_directory': str(output_dir) if output_dir else None,
                'total_files': len(detections),
                'successful': sum(1 for d in detections if d['success']),
                'failed': sum(1 for d in detections if not d['success']),
                'detections': detections
            }, f, indent=2)

        logger.info(f"Log files created: {csv_path.name} and {json_path.name}")

        return csv_path

    def preview_batch(
        self,
        image_dir: Path,
        pattern: str = "*.jpg"
    ) -> List[dict]:
        """
        Preview what would happen when renaming files without actually renaming.

        Args:
            image_dir: Directory containing images
            pattern: Glob pattern for matching files

        Returns:
            List of preview results with original names and proposed new names
        """
        image_dir = Path(image_dir)
        image_files = sorted(image_dir.glob(pattern))

        previews = []
        for img_path in image_files:
            result = self.detector.detect(img_path)

            if result.is_valid:
                new_name = result.get_filename(img_path.suffix.lstrip('.'))
                status = "✓ Ready"
            else:
                new_name = "N/A"
                status = "✗ Detection failed"

            previews.append({
                'original': img_path.name,
                'new_name': new_name,
                'site': result.site_number or "Not found",
                'artifact': result.artifact_number or "Not found",
                'status': status
            })

        return previews
