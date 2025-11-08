"""
Unit tests for the detector module.
"""

import pytest
from pathlib import Path
from nunalleq_ocr.detector import ArtifactDetector, DetectionResult


class TestDetectionResult:
    """Tests for DetectionResult class."""

    def test_is_valid_with_both_numbers(self):
        """Test that result is valid when both numbers are present."""
        result = DetectionResult(
            site_number="GDN-248",
            artifact_number="76656"
        )
        assert result.is_valid is True

    def test_is_valid_with_missing_site(self):
        """Test that result is invalid when site number is missing."""
        result = DetectionResult(
            site_number=None,
            artifact_number="76656"
        )
        assert result.is_valid is False

    def test_is_valid_with_missing_artifact(self):
        """Test that result is invalid when artifact number is missing."""
        result = DetectionResult(
            site_number="GDN-248",
            artifact_number=None
        )
        assert result.is_valid is False

    def test_get_filename_success(self):
        """Test filename generation with valid data."""
        result = DetectionResult(
            site_number="GDN-248",
            artifact_number="76656"
        )
        assert result.get_filename("jpg") == "gdn248_76656.jpg"

    def test_get_filename_different_extension(self):
        """Test filename generation with different extension."""
        result = DetectionResult(
            site_number="GDN-248",
            artifact_number="76656"
        )
        assert result.get_filename("png") == "gdn248_76656.png"

    def test_get_filename_invalid(self):
        """Test filename generation with invalid data."""
        result = DetectionResult(
            site_number=None,
            artifact_number="76656"
        )
        assert result.get_filename("jpg") is None


class TestArtifactDetector:
    """Tests for ArtifactDetector class."""

    def test_initialization_default(self):
        """Test detector initialization with defaults."""
        detector = ArtifactDetector()
        assert detector.site_pattern is not None

    def test_initialization_custom_pattern(self):
        """Test detector initialization with custom pattern."""
        custom_pattern = r"ABC[-\s]?\d+"
        detector = ArtifactDetector(site_pattern=custom_pattern)
        assert detector.site_pattern.pattern == custom_pattern

    def test_parse_site_number_standard_format(self):
        """Test parsing site number in standard format."""
        detector = ArtifactDetector()
        text = "GDN-248 12345"

        result = detector.parse_site_number(text)
        assert result == "GDN-248"

    def test_parse_site_number_no_hyphen(self):
        """Test parsing site number without hyphen."""
        detector = ArtifactDetector()
        text = "GDN248 12345"

        result = detector.parse_site_number(text)
        assert result == "GDN-248"

    def test_parse_site_number_lowercase(self):
        """Test parsing site number in lowercase."""
        detector = ArtifactDetector()
        text = "gdn-248 12345"

        result = detector.parse_site_number(text)
        assert result.upper() == "GDN-248"

    def test_parse_site_number_not_found(self):
        """Test parsing when site number is not present."""
        detector = ArtifactDetector()
        text = "ABCD-123 45678"

        result = detector.parse_site_number(text)
        assert result is None

    def test_parse_artifact_number_no_spaces(self):
        """Test parsing artifact number without spaces."""
        detector = ArtifactDetector()
        text = "GDN-248 76656"

        result = detector.parse_artifact_number(text)
        assert result == "76656"

    def test_parse_artifact_number_with_spaces(self):
        """Test parsing artifact number with spaces between digits."""
        detector = ArtifactDetector()
        text = "GDN-248 7 6 6 5 6"

        result = detector.parse_artifact_number(text)
        assert result == "76656"

    def test_parse_artifact_number_six_digits(self):
        """Test parsing 6-digit artifact number."""
        detector = ArtifactDetector()
        text = "GDN-248 123456"

        result = detector.parse_artifact_number(text)
        assert result == "123456"

    def test_parse_artifact_number_seven_digits(self):
        """Test parsing 7-digit artifact number."""
        detector = ArtifactDetector()
        text = "GDN-248 1234567"

        result = detector.parse_artifact_number(text)
        assert result == "1234567"

    def test_parse_artifact_number_not_found(self):
        """Test parsing when artifact number is not present."""
        detector = ArtifactDetector()
        text = "GDN-248 ABC"

        result = detector.parse_artifact_number(text)
        assert result is None

    def test_detect_nonexistent_file(self):
        """Test detection on nonexistent file."""
        detector = ArtifactDetector()
        result = detector.detect(Path("nonexistent.jpg"))

        assert result.is_valid is False
        assert "Error" in result.raw_text

    @pytest.mark.skipif(
        not Path("images/DSC_3288.jpg").exists(),
        reason="Sample image not found"
    )
    def test_detect_real_image_dsc3288(self):
        """Test detection on real sample image DSC_3288.jpg."""
        detector = ArtifactDetector()
        result = detector.detect(Path("images/DSC_3288.jpg"))

        # This test may need adjustment based on actual OCR performance
        # The expected values are based on the sample images
        assert result.site_number is not None
        assert result.artifact_number is not None

        # If OCR is working well, we should get these values
        if result.is_valid:
            assert "GDN" in result.site_number.upper()
            assert result.artifact_number.isdigit()

    @pytest.mark.skipif(
        not Path("images/DSC_2188.jpg").exists(),
        reason="Sample image not found"
    )
    def test_detect_real_image_dsc2188(self):
        """Test detection on real sample image DSC_2188.jpg."""
        detector = ArtifactDetector()
        result = detector.detect(Path("images/DSC_2188.jpg"))

        # This test may need adjustment based on actual OCR performance
        assert result.site_number is not None
        assert result.artifact_number is not None

        if result.is_valid:
            assert "GDN" in result.site_number.upper()
            assert result.artifact_number.isdigit()
