# Decisions

## Summary

This solution productionizes the starter prototype by separating the runner from the reusable pipeline, validating startup configuration, isolating field detection behind an interface, sampling frames for efficiency, handling invalid detections explicitly, reporting job progress and completion to the mock API, and preparing Docker-ready service files.

## Assumptions And Open Questions

- The provided detector is a placeholder for a real sport-specific model.
- Missing or invalid pitch boundaries are expected in real feeds and should not crash the whole run.
- Long videos do not need every frame analyzed to produce useful operational metrics.
- The mock API represents the platform reporting contract, but a production API would likely have stricter schema, authentication, retries, and monitoring.

Open questions:

- What minimum detection confidence is acceptable for production?
- Should reporting failure ever fail the job, or should it always be best-effort?
- What final aggregation does the downstream crop system need?
- How often should progress be reported for very long videos?

## Validation Strictness Versus Fallback

The application fails fast for invalid configuration, unsupported detector settings, unsupported crop settings, missing reporting URL when reporting is enabled, and video input that cannot be opened.

The application allows frame-level fallback for missing or invalid detections because real broadcast feeds can include close-ups, blank frames, occlusions, and camera cuts.

## Performance Tradeoffs

The pipeline samples frames instead of processing every frame. This improves throughput for long videos while preserving representative detections for the assignment scenario.

Reusable geometry, such as the outer frame boundary, is created once per run rather than repeatedly inside every valid-frame path.

## Detector Boundary

I did not attempt to improve the synthetic field-detection algorithm because the assignment frames it as a placeholder. I kept the current green-mask detector behavior as the default implementation and isolated it behind a detector interface so a sport-specific or ML-backed detector can replace it later.

## Reporting Behavior

The pipeline reports progress and final outcome to the mock API over HTTP. Reporting payloads are validated before being sent.

Reporting failures are handled separately from video-processing failures in the application code. By default, if the runner is started locally and the reporting service is unavailable, the outage is logged and the video pipeline continues. This prevents a platform/network issue from being silently treated as a detector or video failure.

In Docker Compose, the runner is configured to wait for the mock API health check before starting. That matches the assignment's expected container workflow, where the reporting service is part of the composed system.

## Docker Verification Note

The repository includes a Dockerfile and docker-compose configuration for running the mock API and pipeline runner together.

Due to a local machine limitation preventing WSL/Docker from running, I could not execute the Docker Compose workflow locally. I verified the equivalent runtime path using local Python by running the Flask mock API and sending progress/completion events to it over HTTP.

## AI/LLM Disclosure

I used ChatGPT as an engineering assistant during this assignment. I used it to interpret the assignment requirements, identify production-readiness concerns in the starter prototype, outline the implementation plan, and draft documentation language for decisions and AI disclosure.

I reviewed and adapted all suggestions manually. Final implementation decisions, code structure, error behavior, tests, and documentation were written or adjusted by me.
