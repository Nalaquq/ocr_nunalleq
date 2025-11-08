"""
Nunalleq OCR - Artifact Photo Organization System

A Python package for detecting site numbers and artifact numbers from
archaeological artifact photos using OCR, designed for the Nunalleq museum.
"""

__version__ = "0.1.0"
__author__ = "Nunalleq Museum Project"

from .detector import ArtifactDetector, DetectionResult
from .renamer import ArtifactRenamer

__all__ = ["ArtifactDetector", "DetectionResult", "ArtifactRenamer"]
