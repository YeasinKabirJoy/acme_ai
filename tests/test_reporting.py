"""Tests for reporting payloads and HTTP client behavior."""

from unittest.mock import Mock, patch

import pytest
import requests
from pydantic import ValidationError

from pitch_pipeline.config import ReportingConfig
from pitch_pipeline.errors import ReportingError
from pitch_pipeline.models import PipelineMetrics, PipelineResult
from pitch_pipeline.reporting import HttpJobReporter, JobEvent, ProgressReport


def test_progress_report_with_invalid_percent_raises_validation_error() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        ProgressReport(
            job_id="job-1",
            frames_seen=10,
            frames_sampled=1,
            valid_detections=1,
            invalid_detections=0,
            failed_frames=0,
            progress_percent=101,
        )


def test_job_event_with_completed_type_accepts_metrics() -> None:
    # Arrange / Act
    event = JobEvent(
        job_id="job-1",
        event_type="completed",
        message="done",
        metrics={"frames_seen": 10},
    )

    # Assert
    assert event.event_type == "completed"
    assert event.metrics["frames_seen"] == 10


@patch("pitch_pipeline.reporting.requests.post")
def test_report_completion_with_result_posts_event_payload(post: Mock) -> None:
    # Arrange
    post.return_value = create_response()
    reporter = HttpJobReporter(ReportingConfig(base_url="http://example.test", job_id="job-1"))
    metrics = PipelineMetrics(total_frames=10, frames_seen=10, frames_sampled=3)
    result = PipelineResult(metrics=metrics, frame_results=[])

    # Act
    reporter.report_completion(result)

    # Assert
    post.assert_called_once()
    payload = post.call_args.kwargs["json"]
    assert post.call_args.args[0] == "http://example.test/api/v1/jobs/events"
    assert payload["event_type"] == "completed"
    assert payload["metrics"]["frames_seen"] == 10


@patch("pitch_pipeline.reporting.requests.post")
def test_report_progress_with_required_reporting_failure_raises_reporting_error(post: Mock) -> None:
    # Arrange
    post.side_effect = requests.ConnectionError("offline")
    reporter = HttpJobReporter(
        ReportingConfig(
            base_url="http://example.test",
            fail_pipeline_on_error=True,
        )
    )
    metrics = PipelineMetrics(total_frames=10, frames_seen=1, frames_sampled=1)

    # Act / Assert
    with pytest.raises(ReportingError):
        reporter.report_progress(metrics)


def create_response() -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None

    return response
