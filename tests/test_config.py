"""Tests for pipeline configuration validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pitch_pipeline.config import (
    DetectorConfig,
    FrameSamplingConfig,
    PipelineConfig,
    ReportingConfig,
)


def test_pipeline_config_with_unknown_field_raises_validation_error() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PipelineConfig(unexpected=True)


def test_reporting_config_with_enabled_and_missing_base_url_raises_validation_error() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="base_url is required"):
        ReportingConfig(enabled=True)


def test_detector_config_with_unsupported_sport_raises_validation_error() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="unsupported sport"):
        DetectorConfig(sport="tennis")


def test_frame_interval_with_thirty_fps_source_returns_sample_interval() -> None:
    # Arrange
    config = FrameSamplingConfig(analysis_fps=2)

    # Act
    interval = config.frame_interval(source_fps=30)

    # Assert
    assert interval == 15


def test_pipeline_config_with_video_path_accepts_path_value() -> None:
    # Arrange
    video_path = Path("custom.mp4")

    # Act
    config = PipelineConfig(video_path=video_path)

    # Assert
    assert config.video_path == video_path
