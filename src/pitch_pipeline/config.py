"""Validated configuration for the pitch pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, model_validator

from pitch_pipeline.constants import (
    DEFAULT_ANALYSIS_FPS,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_GENERATED_FPS,
    DEFAULT_GENERATED_FRAME_COUNT,
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_JOB_ID,
    DEFAULT_MIN_FIELD_AREA,
    DEFAULT_PADDING_PX,
    DEFAULT_PROGRESS_INTERVAL_SECONDS,
    DEFAULT_REPORTING_TIMEOUT_SECONDS,
    DEFAULT_VIDEO_PATH,
    MASK_DETECTOR_TYPE,
    SUPPORTED_ASPECT_RATIO,
    SUPPORTED_SPORT,
)


class StrictModel(BaseModel):
    """Base model that rejects misspelled or unexpected configuration fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GeneratedVideoConfig(StrictModel):
    """Settings used when a synthetic video must be generated locally."""

    enabled: bool = True
    frame_count: int = Field(default=DEFAULT_GENERATED_FRAME_COUNT, gt=0)
    fps: float = Field(default=DEFAULT_GENERATED_FPS, gt=0)
    width: int = Field(default=DEFAULT_IMAGE_WIDTH, gt=0)
    height: int = Field(default=DEFAULT_IMAGE_HEIGHT, gt=0)
    seed: int = 42


class FrameSamplingConfig(StrictModel):
    """Controls how many frames are analyzed from a video feed."""

    analysis_fps: float = Field(default=DEFAULT_ANALYSIS_FPS, gt=0)

    def frame_interval(self, source_fps: float) -> int:
        """Return the frame interval for the configured analysis rate."""

        if source_fps <= 0:
            return 1

        return max(1, round(source_fps / self.analysis_fps))


class DetectorConfig(StrictModel):
    """Configuration for the default synthetic field detector."""

    detector_type: str = MASK_DETECTOR_TYPE
    sport: str = SUPPORTED_SPORT
    min_area: float = Field(default=DEFAULT_MIN_FIELD_AREA, gt=0)
    confidence_threshold: float = Field(default=DEFAULT_CONFIDENCE_THRESHOLD, ge=0, le=1)

    @model_validator(mode="after")
    def validate_supported_detector(self) -> Self:
        """Reject detector settings the starter implementation cannot support."""

        if self.detector_type != MASK_DETECTOR_TYPE:
            raise ValueError(f"unsupported detector_type: {self.detector_type}")

        if self.sport != SUPPORTED_SPORT:
            raise ValueError(f"unsupported sport: {self.sport}")

        return self


class CropConfig(StrictModel):
    """Configuration for crop recommendation inputs produced by detections."""

    aspect_ratio: str = SUPPORTED_ASPECT_RATIO
    padding_px: int = Field(default=DEFAULT_PADDING_PX, ge=0)

    @model_validator(mode="after")
    def validate_supported_crop(self) -> Self:
        """Reject crop settings the starter implementation cannot support."""

        if self.aspect_ratio != SUPPORTED_ASPECT_RATIO:
            raise ValueError(f"unsupported aspect_ratio: {self.aspect_ratio}")

        return self


class ReportingConfig(StrictModel):
    """Settings for progress and completion reporting to the mock API."""

    enabled: bool = True
    base_url: HttpUrl | None = None
    job_id: str = Field(default=DEFAULT_JOB_ID, min_length=1)
    progress_interval_seconds: float = Field(default=DEFAULT_PROGRESS_INTERVAL_SECONDS, gt=0)
    timeout_seconds: float = Field(default=DEFAULT_REPORTING_TIMEOUT_SECONDS, gt=0)
    fail_pipeline_on_error: bool = False

    @model_validator(mode="after")
    def require_url_when_enabled(self) -> Self:
        """Ensure reporting cannot silently run without a destination URL."""

        if self.enabled and self.base_url is None:
            raise ValueError("base_url is required when reporting is enabled")

        return self


class LoggingConfig(StrictModel):
    """Logging and diagnostic settings."""

    debug_mode: bool = False


class PipelineConfig(StrictModel):
    """Top-level application configuration."""

    video_path: Path = Path(DEFAULT_VIDEO_PATH)
    generated_video: GeneratedVideoConfig = Field(default_factory=GeneratedVideoConfig)
    frame_sampling: FrameSamplingConfig = Field(default_factory=FrameSamplingConfig)
    detector: DetectorConfig = Field(default_factory=DetectorConfig)
    crop: CropConfig = Field(default_factory=CropConfig)
    reporting: ReportingConfig = Field(
        default_factory=lambda: ReportingConfig(base_url="http://localhost:5000")
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config_from_environment() -> PipelineConfig:
    """Build pipeline configuration from safe defaults and environment overrides."""

    reporting_url = os.getenv("MOCK_API_URL", "http://localhost:5000")
    job_id = os.getenv("JOB_ID", DEFAULT_JOB_ID)
    video_path = Path(os.getenv("VIDEO_PATH", DEFAULT_VIDEO_PATH))

    return PipelineConfig(
        video_path=video_path,
        reporting=ReportingConfig(base_url=reporting_url, job_id=job_id),
    )


def format_validation_error(error: ValidationError) -> str:
    """Create a clear one-line message for startup configuration failures."""

    messages = []

    for issue in error.errors():
        path = ".".join(str(part) for part in issue["loc"])
        messages.append(f"{path}: {issue['msg']}")

    return "; ".join(messages)

