"""Core video processing pipeline."""

from __future__ import annotations

import logging
from time import perf_counter

import cv2
from shapely.geometry import Polygon

from pitch_pipeline.config import PipelineConfig
from pitch_pipeline.detector import FieldDetector
from pitch_pipeline.errors import VideoInputError
from pitch_pipeline.models import FrameResult, PipelineMetrics, PipelineResult
from pitch_pipeline.reporting import JobReporter, NullJobReporter

logger = logging.getLogger(__name__)
DEFAULT_SOURCE_FPS = 30.0


class PitchBoundaryPipeline:
    """Process a video feed and collect pitch boundary detections."""

    def __init__(
        self,
        config: PipelineConfig,
        detector: FieldDetector,
        reporter: JobReporter | None = None,
    ) -> None:
        self._config = config
        self._detector = detector
        self._reporter = reporter or NullJobReporter()

    def run(self) -> PipelineResult:
        """Run the configured pipeline against the configured video path."""

        capture = cv2.VideoCapture(str(self._config.video_path))

        if not capture.isOpened():
            raise VideoInputError(f"could not open video: {self._config.video_path}")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        metrics = PipelineMetrics(total_frames=total_frames)
        frame_results: list[FrameResult] = []

        try:
            self._process_capture(capture, metrics, frame_results)
        finally:
            capture.release()
            metrics.finish()

        logger.info(
            "pipeline completed: frames_seen=%s frames_sampled=%s valid_detections=%s",
            metrics.frames_seen,
            metrics.frames_sampled,
            metrics.valid_detections,
        )

        return PipelineResult(metrics=metrics, frame_results=frame_results)

    def _process_capture(
        self,
        capture: cv2.VideoCapture,
        metrics: PipelineMetrics,
        frame_results: list[FrameResult],
    ) -> None:
        source_fps = capture.get(cv2.CAP_PROP_FPS) or DEFAULT_SOURCE_FPS
        frame_interval = self._config.frame_sampling.frame_interval(source_fps)
        outer_boundary = self._build_outer_boundary(capture)
        next_report_at = perf_counter()

        while True:
            has_frame, frame = capture.read()

            if not has_frame:
                return

            metrics.frames_seen += 1

            if not self._should_sample_frame(metrics.frames_seen, frame_interval):
                metrics.frames_skipped += 1
                continue

            metrics.frames_sampled += 1
            self._process_sampled_frame(metrics, frame_results, outer_boundary, frame)
            next_report_at = self._report_progress_when_due(metrics, next_report_at)

    def _process_sampled_frame(
        self,
        metrics: PipelineMetrics,
        frame_results: list[FrameResult],
        outer_boundary: Polygon,
        frame: cv2.typing.MatLike,
    ) -> None:
        try:
            detection = self._detector.detect(frame)
        except cv2.error:
            metrics.failed_frames += 1
            logger.exception("detector failed on sampled frame")
            return

        if not detection.is_valid or detection.polygon is None:
            metrics.invalid_detections += 1
            logger.debug("invalid detection: reason=%s", detection.reason)
            return

        intersection_area = detection.polygon.intersection(outer_boundary).area
        frame_results.append(
            FrameResult(
                frame_number=metrics.frames_seen,
                polygon=detection.polygon,
                intersection_area=intersection_area,
            )
        )
        metrics.valid_detections += 1

    def _build_outer_boundary(self, capture: cv2.VideoCapture) -> Polygon:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or self._config.generated_video.width
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self._config.generated_video.height

        return Polygon([(0, 0), (width, 0), (width, height), (0, height)])

    def _should_sample_frame(self, frame_number: int, frame_interval: int) -> bool:
        return frame_number == 1 or frame_number % frame_interval == 0

    def _report_progress_when_due(self, metrics: PipelineMetrics, next_report_at: float) -> float:
        now = perf_counter()

        if now < next_report_at:
            return next_report_at

        self._reporter.report_progress(metrics)

        return now + self._config.reporting.progress_interval_seconds
