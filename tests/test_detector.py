"""Tests for the default mask-based field detector."""

import cv2
import numpy as np

from pitch_pipeline.config import DetectorConfig
from pitch_pipeline.detector import MaskFieldDetector


def test_detect_with_blank_frame_returns_invalid_detection() -> None:
    # Arrange
    detector = MaskFieldDetector(DetectorConfig())
    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    # Act
    result = detector.detect(frame)

    # Assert
    assert result.is_valid is False
    assert result.reason == "no_contours"


def test_detect_with_green_field_returns_valid_detection() -> None:
    # Arrange
    detector = MaskFieldDetector(DetectorConfig(min_area=100))
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    cv2.rectangle(frame, (20, 20), (140, 100), (34, 139, 34), thickness=-1)

    # Act
    result = detector.detect(frame)

    # Assert
    assert result.is_valid is True
    assert result.polygon is not None
    assert result.polygon.area > 100
