"""Field detector interface and default mask-based implementation."""

from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np
from shapely.geometry import Polygon

from pitch_pipeline.config import DetectorConfig
from pitch_pipeline.models import DetectionResult

LOWER_GREEN_HSV = np.array([35, 40, 40])
UPPER_GREEN_HSV = np.array([85, 255, 255])
MIN_POLYGON_POINTS = 3


class FieldDetector(Protocol):
    """Interface for sport-specific field boundary detectors."""

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Detect a pitch boundary in a video frame."""


class MaskFieldDetector:
    """Default synthetic detector based on green-mask thresholding."""

    def __init__(self, config: DetectorConfig) -> None:
        self._config = config

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Return a detected field polygon or an invalid detection result."""

        mask = self._extract_mask(frame)

        return self._derive_polygon_from_mask(mask)

    def _extract_mask(self, frame: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        return cv2.inRange(hsv, LOWER_GREEN_HSV, UPPER_GREEN_HSV)

    def _derive_polygon_from_mask(self, mask: np.ndarray) -> DetectionResult:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return DetectionResult(is_valid=False, reason="no_contours")

        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)

        if contour_area <= self._config.min_area:
            return DetectionResult(is_valid=False, reason="area_below_minimum")

        points = largest_contour.reshape(-1, 2)

        if len(points) < MIN_POLYGON_POINTS:
            return DetectionResult(is_valid=False, reason="not_enough_points")

        polygon = Polygon(points)

        if not polygon.is_valid:
            return DetectionResult(is_valid=False, reason="invalid_polygon")

        return DetectionResult(is_valid=True, polygon=polygon)

