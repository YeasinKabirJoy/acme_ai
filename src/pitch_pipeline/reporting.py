"""Validated reporting client for the mock platform API."""

from __future__ import annotations

import logging
from typing import Literal, Protocol

import requests
from pydantic import BaseModel, ConfigDict, Field

from pitch_pipeline.config import ReportingConfig
from pitch_pipeline.errors import ReportingError
from pitch_pipeline.models import PipelineMetrics, PipelineResult

logger = logging.getLogger(__name__)
PROGRESS_ENDPOINT = "/api/v1/jobs/progress"
EVENTS_ENDPOINT = "/api/v1/jobs/events"


class ReportingPayload(BaseModel):
    """Base class for validated outbound reporting payloads."""

    model_config = ConfigDict(extra="forbid")


class ProgressReport(ReportingPayload):
    """Progress payload sent while a job is running."""

    job_id: str = Field(min_length=1)
    frames_seen: int = Field(ge=0)
    frames_sampled: int = Field(ge=0)
    valid_detections: int = Field(ge=0)
    invalid_detections: int = Field(ge=0)
    failed_frames: int = Field(ge=0)
    progress_percent: float = Field(ge=0, le=100)
    status: Literal["running"] = "running"


class JobEvent(ReportingPayload):
    """Final job event payload sent when a job completes or fails."""

    job_id: str = Field(min_length=1)
    event_type: Literal["completed", "failed"]
    message: str = Field(min_length=1)
    metrics: dict[str, float | int] = Field(default_factory=dict)


class JobReporter(Protocol):
    """Interface for job progress and completion reporting."""

    def report_progress(self, metrics: PipelineMetrics) -> None:
        """Report in-progress pipeline metrics."""

    def report_completion(self, result: PipelineResult) -> None:
        """Report successful pipeline completion."""

    def report_failure(self, message: str, metrics: PipelineMetrics | None = None) -> None:
        """Report pipeline failure."""


class NullJobReporter:
    """Reporter used when platform reporting is disabled."""

    def report_progress(self, metrics: PipelineMetrics) -> None:
        """Ignore progress updates."""

    def report_completion(self, result: PipelineResult) -> None:
        """Ignore completion events."""

    def report_failure(self, message: str, metrics: PipelineMetrics | None = None) -> None:
        """Ignore failure events."""


class HttpJobReporter:
    """HTTP reporter for the assignment's mock API."""

    def __init__(self, config: ReportingConfig) -> None:
        if config.base_url is None:
            raise ReportingError("reporting base_url is required")

        self._config = config
        self._base_url = str(config.base_url).rstrip("/")
        self._is_available = True

    def report_progress(self, metrics: PipelineMetrics) -> None:
        """Send a progress update to the mock API."""

        payload = ProgressReport(
            job_id=self._config.job_id,
            frames_seen=metrics.frames_seen,
            frames_sampled=metrics.frames_sampled,
            valid_detections=metrics.valid_detections,
            invalid_detections=metrics.invalid_detections,
            failed_frames=metrics.failed_frames,
            progress_percent=round(metrics.progress_percent, 2),
        )
        self._post(PROGRESS_ENDPOINT, payload)

    def report_completion(self, result: PipelineResult) -> None:
        """Send a completion event to the mock API."""

        payload = JobEvent(
            job_id=self._config.job_id,
            event_type="completed",
            message="Pipeline completed successfully",
            metrics=result.metrics.to_summary(),
        )
        self._post(EVENTS_ENDPOINT, payload)

    def report_failure(self, message: str, metrics: PipelineMetrics | None = None) -> None:
        """Send a failure event to the mock API."""

        payload = JobEvent(
            job_id=self._config.job_id,
            event_type="failed",
            message=message,
            metrics=metrics.to_summary() if metrics is not None else {},
        )
        self._post(EVENTS_ENDPOINT, payload)

    def _post(self, endpoint: str, payload: ReportingPayload) -> None:
        if not self._is_available:
            return

        url = f"{self._base_url}{endpoint}"

        try:
            response = requests.post(
                url,
                json=payload.model_dump(mode="json"),
                timeout=self._config.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            reporting_error = ReportingError(f"failed to report to {url}")

            if self._config.fail_pipeline_on_error:
                raise reporting_error from error

            self._is_available = False
            logger.warning("%s", reporting_error)
