"""
Unit tests for the renamer module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from nunalleq_ocr.detector import ArtifactDetector, DetectionResult
from nunalleq_ocr.renamer import ArtifactRenamer


class MockDetector:
    """Mock detector for testing."""

    def __init__(self, site="GDN-248", artifact="76656"):
        self.site = site
        self.artifact = artifact

    def detect(self, image_path):
        """Return a mock detection result."""
        return DetectionResult(
            site_number=self.site,
            artifact_number=self.artifact,
            raw_text=f"{self.site} {self.artifact}"
        )


class TestArtifactRenamer:
    """Tests for ArtifactRenamer class."""

    def test_initialization_default(self):
        """Test renamer initialization with defaults."""
        renamer = ArtifactRenamer()
        assert renamer.detector is not None
        assert renamer.dry_run is False
        assert renamer.backup is True

    def test_initialization_custom(self):
        """Test renamer initialization with custom settings."""
        detector = MockDetector()
        renamer = ArtifactRenamer(
            detector=detector,
            dry_run=True,
            backup=False
        )
        assert renamer.detector is detector
        assert renamer.dry_run is True
        assert renamer.backup is False

    def test_rename_file_nonexistent(self):
        """Test renaming nonexistent file."""
        detector = MockDetector()
        renamer = ArtifactRenamer(detector=detector)

        success, message = renamer.rename_file(Path("nonexistent.jpg"))

        assert success is False
        assert "not found" in message.lower()

    def test_rename_file_dry_run(self):
        """Test renaming in dry run mode."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            temp_path = Path(tf.name)

        try:
            detector = MockDetector()
            renamer = ArtifactRenamer(detector=detector, dry_run=True)

            success, message = renamer.rename_file(temp_path)

            # File should still exist with original name
            assert temp_path.exists()
            assert success is True
            assert "DRY RUN" in message

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_rename_file_success(self):
        """Test successful file renaming."""
        # Create a temporary directory and file
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_file = tmpdir / "test_image.jpg"
            original_file.write_text("test")

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector, backup=False)

            success, message = renamer.rename_file(original_file)

            # Check that file was renamed
            assert success is True
            assert not original_file.exists()

            expected_name = tmpdir / "gdn248_76656.jpg"
            assert expected_name.exists()

    def test_rename_file_with_output_dir(self):
        """Test renaming with output to different directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_file = tmpdir / "test_image.jpg"
            original_file.write_text("test")

            output_dir = tmpdir / "output"

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector, backup=False)

            success, message = renamer.rename_file(
                original_file,
                output_dir=output_dir
            )

            # Check that file was copied to output directory
            assert success is True
            assert original_file.exists()  # Original still exists when using output_dir

            expected_name = output_dir / "gdn248_76656.jpg"
            assert expected_name.exists()

    def test_rename_file_overwrite_protection(self):
        """Test that existing files are not overwritten by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_file = tmpdir / "test_image.jpg"
            original_file.write_text("test")

            existing_file = tmpdir / "gdn248_76656.jpg"
            existing_file.write_text("existing")

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector, backup=False)

            success, message = renamer.rename_file(original_file, overwrite=False)

            # Should fail because file already exists
            assert success is False
            assert "already exists" in message.lower()
            assert existing_file.read_text() == "existing"

    def test_rename_file_with_overwrite(self):
        """Test renaming with overwrite enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_file = tmpdir / "test_image.jpg"
            original_file.write_text("new content")

            existing_file = tmpdir / "gdn248_76656.jpg"
            existing_file.write_text("old content")

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector, backup=False)

            success, message = renamer.rename_file(original_file, overwrite=True)

            # Should succeed and overwrite existing file
            assert success is True
            assert existing_file.exists()
            assert existing_file.read_text() == "new content"

    def test_rename_batch_success(self):
        """Test batch renaming of multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test files
            (tmpdir / "image1.jpg").write_text("test1")
            (tmpdir / "image2.jpg").write_text("test2")

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector, backup=False)

            results = renamer.rename_batch(tmpdir, pattern="*.jpg")

            assert results['total'] == 2
            assert results['success'] >= 0
            assert results['failed'] >= 0
            assert len(results['results']) == 2

    def test_rename_batch_empty_directory(self):
        """Test batch renaming on empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            detector = MockDetector()
            renamer = ArtifactRenamer(detector=detector)

            results = renamer.rename_batch(tmpdir, pattern="*.jpg")

            assert results['total'] == 0
            assert results['success'] == 0
            assert results['failed'] == 0

    def test_preview_batch(self):
        """Test preview functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test files
            (tmpdir / "image1.jpg").write_text("test1")
            (tmpdir / "image2.jpg").write_text("test2")

            detector = MockDetector(site="GDN-248", artifact="76656")
            renamer = ArtifactRenamer(detector=detector)

            previews = renamer.preview_batch(tmpdir, pattern="*.jpg")

            assert len(previews) == 2
            for preview in previews:
                assert 'original' in preview
                assert 'new_name' in preview
                assert 'site' in preview
                assert 'artifact' in preview
                assert 'status' in preview
