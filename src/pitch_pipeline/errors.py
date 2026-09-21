"""Domain-specific errors for the pitch pipeline."""


class PipelineError(Exception):
    """Base class for pipeline failures."""


class ConfigurationError(PipelineError):
    """Raised when startup configuration is invalid."""


class VideoInputError(PipelineError):
    """Raised when the video input cannot be opened or read."""


class ReportingError(PipelineError):
    """Raised when reporting to the platform fails."""

