"""
OCR Detection module for extracting site and artifact numbers from images.
"""

import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Container for OCR detection results."""

    site_number: Optional[str] = None
    artifact_number: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Check if both site and artifact numbers were detected."""
        return self.site_number is not None and self.artifact_number is not None

    def get_filename(self, extension: str = "jpg") -> Optional[str]:
        """
        Generate standardized filename from detected numbers.

        Args:
            extension: File extension without the dot (default: 'jpg')

        Returns:
            Formatted filename like 'gdn248_76656.jpg' or None if invalid
        """
        if not self.is_valid:
            return None

        # Remove hyphens and convert to lowercase for site number
        site = self.site_number.replace("-", "").lower()
        return f"{site}_{self.artifact_number}.{extension}"


class ArtifactDetector:
    """
    OCR-based detector for extracting site and artifact numbers from images.

    This detector is optimized for archaeological artifact photos with:
    - White or light backgrounds
    - Consistent typeface for labels
    - Site numbers in format like 'GDN-248'
    - Artifact numbers (may have spaces between digits)
    """

    def __init__(
        self,
        site_pattern: str = r"GDN[-\s]?\d+",
        tesseract_cmd: Optional[str] = None
    ):
        """
        Initialize the artifact detector.

        Args:
            site_pattern: Regex pattern for site number (default: GDN-XXX)
            tesseract_cmd: Path to tesseract executable (None = auto-detect)
        """
        self.site_pattern = re.compile(site_pattern, re.IGNORECASE)

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def preprocess_image(self, image: Image.Image, light: bool = True) -> Image.Image:
        """
        Preprocess image to enhance OCR accuracy.

        Args:
            image: PIL Image object
            light: If True, use minimal preprocessing (recommended)

        Returns:
            Preprocessed PIL Image
        """
        if light:
            # Minimal preprocessing - often works better for clean label photos
            # Just convert to grayscale
            return image.convert('L')

        # Heavy preprocessing (fallback option)
        # Convert PIL to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply bilateral filter to reduce noise while keeping edges sharp
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Convert back to PIL Image
        return Image.fromarray(binary)

    def extract_text(self, image_path: Path, preprocess: bool = True) -> str:
        """
        Extract text from image using Tesseract OCR with spatial awareness.

        Uses spatial positioning to extract artifact numbers that appear below
        the site number.

        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess the image (default: True)

        Returns:
            Extracted text string with spatial context
        """
        try:
            image = Image.open(image_path)

            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--oem 3 --psm 11'
            )

            # Build combined text output
            all_text = []

            # Find site number position
            site_y_position = None
            for i, text in enumerate(data['text']):
                text_clean = text.strip()
                if text_clean:
                    all_text.append(text_clean)

                    # Check if this is the site number
                    if 'GDN' in text_clean.upper() or self.site_pattern.match(text_clean):
                        site_y_position = data['top'][i]
                        logger.debug(f"Found site number at y={site_y_position}")

            # Extract text specifically from below the site number
            # Search full range but with smart filtering to avoid noise
            if site_y_position is not None:
                artifact_detections = []

                for i, text in enumerate(data['text']):
                    text_clean = text.strip()
                    if not text_clean:
                        continue

                    y_pos = data['top'][i]
                    x_pos = data['left'][i]
                    conf = int(data['conf'][i])

                    # Look in the full range (50-1200 pixels below site number)
                    if site_y_position + 50 <= y_pos <= site_y_position + 1200:
                        # Be selective: only include high-confidence digits or text that looks like digit boxes
                        # Digit boxes can be garbled (e.g., "7\.2\3)\8" for "77238")
                        is_likely_digit = (
                            (conf > 70 and any(c.isdigit() for c in text_clean)) or  # High conf with digits
                            (conf > 40 and len(text_clean) <= 3 and any(c.isdigit() for c in text_clean)) or  # Short with digits
                            (len(text_clean) <= 12 and all(c.isdigit() or c in '\\/(). -_' for c in text_clean)) or  # Looks like garbled digits
                            (len(text_clean) <= 5 and any(c.isdigit() for c in text_clean) and conf >= 0)  # Short with any digits, any confidence
                        )

                        if is_likely_digit:
                            artifact_detections.append({
                                'text': text_clean,
                                'y': y_pos,
                                'x': x_pos,
                                'conf': conf
                            })
                            logger.debug(f"Artifact detection: '{text_clean}' at (x={x_pos}, y={y_pos}), conf={conf}")

                # Group detections by Y position (within 50 pixels = same row)
                if artifact_detections:
                    artifact_detections.sort(key=lambda d: d['y'])
                    rows = []
                    current_row = [artifact_detections[0]]
                    current_y = artifact_detections[0]['y']

                    for detection in artifact_detections[1:]:
                        if abs(detection['y'] - current_y) < 50:  # Same row
                            current_row.append(detection)
                        else:  # New row
                            rows.append(current_row)
                            current_row = [detection]
                            current_y = detection['y']
                    rows.append(current_row)

                    # For each row, sort by X position and extract digits
                    for row_idx, row in enumerate(rows, 1):
                        row.sort(key=lambda d: d['x'])  # Left to right
                        row_text = ' '.join([d['text'] for d in row])
                        logger.debug(f"Artifact row {row_idx}: {row_text}")
                        all_text.append(f"ARTIFACT_ROW_{row_idx}: {row_text}")

            combined_text = "\n".join(all_text)
            logger.debug(f"Extracted text from {image_path.name}: {combined_text[:200]}")

            return combined_text

        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return ""

    def parse_site_number(self, text: str) -> Optional[str]:
        """
        Extract site number from text using regex.

        Handles cases where "GDN-248" might be split by OCR into separate pieces.

        Args:
            text: OCR-extracted text

        Returns:
            Site number string (e.g., 'GDN-248') or None
        """
        # Strategy 1: Try to find complete site number
        match = self.site_pattern.search(text)
        if match:
            site = match.group(0)
            # Normalize: ensure hyphen is present
            site = re.sub(r'(GDN)[-\s]?(\d+)', r'\1-\2', site, flags=re.IGNORECASE)
            logger.debug(f"Found site number: {site}")
            return site

        # Strategy 2: Look for "GDN" and "248" separately and combine them
        # This handles cases where OCR splits the text
        if re.search(r'\bGDN\b', text, re.IGNORECASE):
            # Found "GDN", now look for "248" nearby
            # Look for patterns like: "24", "8" or "—-24", "8" or "2", "4", "8"
            digits = re.findall(r'\d+', text)

            # Check if we can reconstruct "248" from the digits
            all_digits = ''.join(digits)
            if '248' in all_digits:
                logger.debug(f"Found site number (reconstructed): GDN-248")
                return "GDN-248"

            # Also check for common OCR patterns where 248 might be garbled
            # Look for 24, 2-4, or similar followed by 8
            if any('24' in d or '2' in d and '4' in d for d in digits[:3]) and '8' in all_digits[:10]:
                logger.debug(f"Found site number (pattern match): GDN-248")
                return "GDN-248"

        return None

    def parse_artifact_number(self, text: str) -> Optional[str]:
        """
        Extract artifact number(s) from text.

        Handles cases where digits may have spaces between them (e.g., '7 6 6 5 6'),
        garbled OCR from digit boxes (e.g., '7\.2\3)\8'), multiple rows of artifacts,
        or other OCR noise.

        Args:
            text: OCR-extracted text

        Returns:
            Artifact number string (digits only), or multiple numbers joined with "_" for
            images with multiple artifacts, or None
        """
        # Remove the site number from text to avoid confusion
        text_without_site = self.site_pattern.sub('', text)

        # Strategy 1: Look for multiple artifact rows (from spatial OCR)
        # This handles images with multiple artifacts
        artifact_numbers = []
        row_matches = re.findall(r'ARTIFACT_ROW_(\d+):\s*(.+)', text, re.MULTILINE)

        if row_matches:
            for row_num, row_text in row_matches:
                logger.debug(f"Processing artifact row {row_num}: {row_text}")

                # Extract only digits from this row
                digits_only = re.sub(r'\D', '', row_text)

                # Valid artifact numbers are 5-7 digits
                if 5 <= len(digits_only) <= 7:
                    artifact_numbers.append(digits_only)
                    logger.debug(f"Found artifact number from row {row_num}: {digits_only}")
                elif len(digits_only) > 7:
                    # Might have picked up ruler numbers or extra digits
                    # Try to extract a valid 5-7 digit sequence
                    # Look for the last 5 digits (most common length for artifacts)
                    candidate = digits_only[-5:]
                    artifact_numbers.append(candidate)
                    logger.debug(f"Found artifact number from row {row_num} (truncated to last 5): {candidate}")
                elif len(digits_only) >= 1 and len(digits_only) < 5:
                    # Row has some digits but not enough - this might be noise
                    # Skip this row
                    logger.debug(f"Skipping row {row_num} - only {len(digits_only)} digits: {digits_only}")

            if artifact_numbers:
                # Return multiple artifacts joined with underscore
                result = "_".join(artifact_numbers)
                logger.debug(f"Returning multiple artifacts: {result}")
                return result
            # If no valid artifacts found in rows, continue to fallback strategies

        # Strategy 2: Look for old-style ARTIFACT_REGION marker (backward compatibility)
        artifact_region_match = re.search(r'ARTIFACT_REGION:\s*(.+)', text, re.MULTILINE)
        if artifact_region_match:
            artifact_region = artifact_region_match.group(1)
            logger.debug(f"Found artifact region: {artifact_region}")

            # Extract all digits from the artifact region
            digits_only = re.sub(r'\D', '', artifact_region)

            if 5 <= len(digits_only) <= 7:
                logger.debug(f"Found artifact number (spatial region): {digits_only}")
                return digits_only
            elif len(digits_only) > 7:
                # Take last 5-7 digits (most likely the actual artifact number)
                artifact_num = digits_only[-7:] if len(digits_only) >= 7 else digits_only[-5:]
                logger.debug(f"Found artifact number (spatial region, truncated): {artifact_num}")
                return artifact_num

        # Strategy 3: Look for sequences of 5-7 digits with optional spaces/punctuation
        patterns = [
            r'(\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d)',  # 7 digits
            r'(\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d)',              # 6 digits
            r'(\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d[\s\.\-_\\\/\)\(]?\d)',                          # 5 digits
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_without_site)
            for match in matches:
                artifact_num = re.sub(r'\D', '', match)
                if 5 <= len(artifact_num) <= 7:
                    logger.debug(f"Found artifact number (pattern match): {artifact_num}")
                    return artifact_num

        # Strategy 4: Find all digit sequences and combine
        digit_sequences = re.findall(r'\d+', text_without_site)
        if digit_sequences:
            combined = []
            for seq in digit_sequences:
                if len(seq) >= 1:
                    combined.append(seq)

            full_number = ''.join(combined)
            if 5 <= len(full_number) <= 10:
                artifact_num = full_number[-7:] if len(full_number) >= 7 else full_number
                if 5 <= len(artifact_num) <= 7:
                    logger.debug(f"Found artifact number (combined sequences): {artifact_num}")
                    return artifact_num

        return None

    def detect(self, image_path: Path) -> DetectionResult:
        """
        Detect site and artifact numbers from an image.

        Args:
            image_path: Path to image file

        Returns:
            DetectionResult object with extracted information
        """
        image_path = Path(image_path)

        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return DetectionResult(raw_text="Error: File not found")

        # Extract text
        raw_text = self.extract_text(image_path)

        if not raw_text.strip():
            logger.warning(f"No text detected in {image_path.name}")
            return DetectionResult(raw_text="")

        # Parse site and artifact numbers
        site_number = self.parse_site_number(raw_text)
        artifact_number = self.parse_artifact_number(raw_text)

        result = DetectionResult(
            site_number=site_number,
            artifact_number=artifact_number,
            raw_text=raw_text,
            confidence=1.0 if site_number and artifact_number else 0.5
        )

        if not result.is_valid:
            logger.warning(
                f"Incomplete detection for {image_path.name}: "
                f"site={site_number}, artifact={artifact_number}"
            )

        return result

    def detect_batch(self, image_paths: list[Path]) -> dict[Path, DetectionResult]:
        """
        Detect numbers from multiple images.

        Args:
            image_paths: List of image file paths

        Returns:
            Dictionary mapping image paths to DetectionResult objects
        """
        results = {}
        for img_path in image_paths:
            results[img_path] = self.detect(img_path)
        return results
