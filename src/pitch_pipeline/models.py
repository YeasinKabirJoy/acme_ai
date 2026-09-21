"""Typed models used by the pitch pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from shapely.geometry import Polygon


@dataclass(frozen=True)
class DetectionResult:
    """Field detector output for one analyzed frame."""

    is_valid: bool
    polygon: Polygon | None = None
    reason: str | None = None


@dataclass(frozen=True)
class FrameResult:
    """Validated output for one sampled frame."""

    frame_number: int
    polygon: Polygon
    intersection_area: float


@dataclass
class PipelineMetrics:
    """Counters describing a pipeline run."""

    total_frames: int = 0
    frames_seen: int = 0
    frames_sampled: int = 0
    frames_skipped: int = 0
    valid_detections: int = 0
    invalid_detections: int = 0
    failed_frames: int = 0
    started_at: float = field(default_factory=perf_counter)
    completed_at: float | None = None

    def finish(self) -> None:
        """Mark the metrics as complete."""

        self.completed_at = perf_counter()

    @property
    def duration_seconds(self) -> float:
        """Return elapsed processing time in seconds."""

        end_time = self.completed_at or perf_counter()

        return end_time - self.started_at

    @property
    def detection_rate(self) -> float:
        """Return the valid detection ratio for sampled frames."""

        if self.frames_sampled == 0:
            return 0.0

        return self.valid_detections / self.frames_sampled

    @property
    def progress_percent(self) -> float:
        """Return approximate video progress as a percentage."""

        if self.total_frames <= 0:
            return 0.0

        return min(100.0, (self.frames_seen / self.total_frames) * 100)

    def to_summary(self) -> dict[str, float | int]:
        """Return serializable metrics for job event payloads."""

        return {
            "total_frames": self.total_frames,
            "frames_seen": self.frames_seen,
            "frames_sampled": self.frames_sampled,
            "frames_skipped": self.frames_skipped,
            "valid_detections": self.valid_detections,
            "invalid_detections": self.invalid_detections,
            "failed_frames": self.failed_frames,
            "duration_seconds": round(self.duration_seconds, 3),
            "detection_rate": round(self.detection_rate, 4),
        }


@dataclass(frozen=True)
class PipelineResult:
    """Final output from one pipeline run."""

    metrics: PipelineMetrics
    frame_results: list[FrameResult]
