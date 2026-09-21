"""Thin command-line entry point for the pitch pipeline."""

from __future__ import annotations

import logging
import sys

from pydantic import ValidationError

from pitch_pipeline.config import PipelineConfig, format_validation_error, load_config_from_environment
from pitch_pipeline.detector import MaskFieldDetector
from pitch_pipeline.errors import PipelineError
from pitch_pipeline.pipeline import PitchBoundaryPipeline
from synthetic_generator import generate_synthetic_video


def main() -> int:
    """Run the pitch boundary pipeline and return a process exit code."""

    try:
        config = load_config_from_environment()
    except ValidationError as error:
        print(f"Invalid configuration: {format_validation_error(error)}", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=logging.DEBUG if config.logging.debug_mode else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        _generate_video_when_needed(config)
        detector = MaskFieldDetector(config.detector)
        pipeline = PitchBoundaryPipeline(config, detector)
        result = pipeline.run()
    except PipelineError as error:
        logging.exception("pipeline failed")
        print(f"Pipeline failed: {error}", file=sys.stderr)
        return 1

    print(
        "Pipeline finished: "
        f"frames_seen={result.metrics.frames_seen}, "
        f"frames_sampled={result.metrics.frames_sampled}, "
        f"valid_detections={result.metrics.valid_detections}, "
        f"invalid_detections={result.metrics.invalid_detections}"
    )

    return 0


def _generate_video_when_needed(config: PipelineConfig) -> None:
    video_path = config.video_path

    if video_path.exists():
        return

    if not config.generated_video.enabled:
        return

    generate_synthetic_video(
        outputPath=str(video_path),
        numFrames=config.generated_video.frame_count,
        imgWidth=config.generated_video.width,
        imgHeight=config.generated_video.height,
        seed=config.generated_video.seed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
