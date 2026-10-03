"""Internal validation helper functions."""

from __future__ import annotations

import math

from .exceptions import AudioTypeError, AudioValueError
from .pcm import PCMChannels, PCMSampleRate


def validate_sample_rate_opt(
    sample_rate: PCMSampleRate | None,
) -> PCMSampleRate | None:
    """Validate optional target sample rate.

    Args:
        sample_rate: Sample rate to validate.

    Returns:
        PCMSampleRate | None: The validated PCMSampleRate or None.

    Raises:
        AudioTypeError: If sample_rate is not PCMSampleRate or None.
    """
    if sample_rate is None:
        return None
    if isinstance(sample_rate, PCMSampleRate):
        return sample_rate
    t_name = type(sample_rate).__name__
    raise AudioTypeError(
        f"sample_rate must be an instance of PCMSampleRate or None, got {t_name}"
    )


def validate_channels_opt(
    channels: PCMChannels | None,
) -> PCMChannels | None:
    """Validate optional target channels.

    Args:
        channels: Channels to validate.

    Returns:
        PCMChannels | None: The validated PCMChannels or None.

    Raises:
        AudioTypeError: If channels is not PCMChannels or None.
    """
    if channels is None:
        return None
    if isinstance(channels, PCMChannels):
        return channels
    t_name = type(channels).__name__
    raise AudioTypeError(
        f"channels must be an instance of PCMChannels or None, got {t_name}"
    )


def validate_start_time(start_time: float | int | None) -> float | None:
    """Validate optional start time offset in seconds.

    Args:
        start_time: Start time in seconds.

    Returns:
        float | None: The validated start time as float or None.

    Raises:
        AudioTypeError: If start_time is of invalid type.
        AudioValueError: If start_time is NaN, infinite, or negative.
    """
    if start_time is None:
        return None
    if not isinstance(start_time, (int, float)) or isinstance(start_time, bool):
        t_name = type(start_time).__name__
        raise AudioTypeError(f"start_time must be a float, int, or None, got {t_name}")
    if math.isnan(start_time) or math.isinf(start_time):
        raise AudioValueError(f"start_time must be a finite number, got {start_time}")
    if start_time < 0:
        raise AudioValueError(f"start_time must be non-negative, got {start_time}")
    return float(start_time)


def validate_duration(duration: float | int | None) -> float | None:
    """Validate optional duration in seconds.

    Args:
        duration: Duration in seconds.

    Returns:
        float | None: The validated duration as float or None.

    Raises:
        AudioTypeError: If duration is of invalid type.
        AudioValueError: If duration is NaN, infinite, or non-positive.
    """
    if duration is None:
        return None
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        t_name = type(duration).__name__
        raise AudioTypeError(f"duration must be a float, int, or None, got {t_name}")
    if math.isnan(duration) or math.isinf(duration):
        raise AudioValueError(f"duration must be a finite number, got {duration}")
    if duration <= 0:
        raise AudioValueError(f"duration must be positive, got {duration}")
    return float(duration)
