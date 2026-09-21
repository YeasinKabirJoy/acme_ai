"""Tests for pipeline frame sampling and metrics."""

import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

from pitch_pipeline.config import (
    FrameSamplingConfig,
    GeneratedVideoConfig,
    PipelineConfig,
    ReportingConfig,
)
from pitch_pipeline.detector import MaskFieldDetector
from pitch_pipeline.pipeline import PitchBoundaryPipeline
from pitch_pipeline.reporting import NullJobReporter


def test_run_with_sampled_video_counts_valid_and_invalid_detections(tmp_path: Path) -> None:
    # Arrange
    video_path = tmp_path / "sample.mp4"
    create_sample_video(video_path)
    config = PipelineConfig(
        video_path=video_path,
        generated_video=GeneratedVideoConfig(enabled=False, width=160, height=120),
        frame_sampling=FrameSamplingConfig(analysis_fps=2),
        reporting=ReportingConfig(enabled=False),
    )
    detector = MaskFieldDetector(config.detector)
    pipeline = PitchBoundaryPipeline(config, detector, NullJobReporter())

    # Act
    result = pipeline.run()

    # Assert
    assert result.metrics.frames_seen == 10
    assert result.metrics.frames_sampled == 3
    assert result.metrics.frames_skipped == 7
    assert result.metrics.valid_detections == 2
    assert result.metrics.invalid_detections == 1
    assert len(result.frame_results) == 2


@pytest.fixture(name="tmp_path")
def create_workspace_temp_path() -> Path:
    path = Path(".test-output") / "pipeline"

    if path.exists():
        shutil.rmtree(path)

    path.mkdir(parents=True)

    yield path

    shutil.rmtree(path, ignore_errors=True)


def create_sample_video(video_path: Path) -> None:
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (160, 120))

    for frame_number in range(1, 11):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)

        if frame_number in {1, 5}:
            frame[:] = (34, 139, 34)

        writer.write(frame)

    writer.release()
