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


def parse_timecode(value: str) -> float:
    """Parse a timecode string into seconds as a float.

    Supported formats:
        - "HH:MM:SS" or "HH:MM:SS.mmm" (e.g. "01:23:45", "00:01:30.500")
        - "MM:SS" or "MM:SS.mmm" (e.g. "02:15", "01:30.250")
        - "SS" or "SS.mmm" (e.g. "90", "12.5")

    Args:
        value: Timecode string.

    Returns:
        float: Parsed time in seconds.

    Raises:
        AudioValueError: If the string is empty or has an invalid timecode format.
    """
    s = value.strip().replace(",", ".")
    if not s:
        raise AudioValueError("Timecode string cannot be empty")

    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            minutes_str, seconds_str = parts
            minutes = int(minutes_str)
            seconds = float(seconds_str)
            if minutes < 0:
                raise AudioValueError(
                    f"Minutes cannot be negative in timecode: '{value}'"
                )
            if not (0.0 <= seconds < 60.0):
                raise AudioValueError(
                    f"Seconds must be in range [0, 60) in timecode: '{value}'"
                )
            return minutes * 60.0 + seconds
        elif len(parts) == 3:
            hours_str, minutes_str, seconds_str = parts
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = float(seconds_str)
            if hours < 0:
                raise AudioValueError(
                    f"Hours cannot be negative in timecode: '{value}'"
                )
            if not (0 <= minutes < 60):
                raise AudioValueError(
                    f"Minutes must be in range [0, 59] in timecode: '{value}'"
                )
            if not (0.0 <= seconds < 60.0):
                raise AudioValueError(
                    f"Seconds must be in range [0, 60) in timecode: '{value}'"
                )
            return hours * 3600.0 + minutes * 60.0 + seconds
        else:
            raise AudioValueError(
                f"Invalid timecode format (expected SS, MM:SS, or HH:MM:SS): '{value}'"
            )
    except ValueError as e:
        if isinstance(e, AudioValueError):
            raise
        raise AudioValueError(f"Invalid timecode string: '{value}'") from e


def validate_start_time(start_time: float | int | str | None) -> float | None:
    """Validate optional start time offset in seconds or timecode string.

    Args:
        start_time: Start time as seconds (float/int) or timecode (str).

    Returns:
        float | None: The validated start time in seconds as float, or None.

    Raises:
        AudioTypeError: If start_time is of invalid type.
        AudioValueError: If start_time is NaN, infinite, negative, or an invalid
            timecode string.
    """
    if start_time is None:
        return None
    if isinstance(start_time, bool) or not isinstance(start_time, (int, float, str)):
        t_name = type(start_time).__name__
        raise AudioTypeError(
            f"start_time must be a float, int, str, or None, got {t_name}"
        )
    if isinstance(start_time, str):
        sec = parse_timecode(start_time)
    else:
        sec = float(start_time)

    if math.isnan(sec) or math.isinf(sec):
        raise AudioValueError(f"start_time must be a finite number, got {start_time}")
    if sec < 0:
        raise AudioValueError(f"start_time must be non-negative, got {start_time}")
    return sec


def validate_duration(duration: float | int | str | None) -> float | None:
    """Validate optional duration in seconds or timecode string.

    Args:
        duration: Duration as seconds (float/int) or timecode (str).

    Returns:
        float | None: The validated duration in seconds as float, or None.

    Raises:
        AudioTypeError: If duration is of invalid type.
        AudioValueError: If duration is NaN, infinite, non-positive, or an invalid
            timecode string.
    """
    if duration is None:
        return None
    if isinstance(duration, bool) or not isinstance(duration, (int, float, str)):
        t_name = type(duration).__name__
        raise AudioTypeError(
            f"duration must be a float, int, str, or None, got {t_name}"
        )
    if isinstance(duration, str):
        sec = parse_timecode(duration)
    else:
        sec = float(duration)

    if math.isnan(sec) or math.isinf(sec):
        raise AudioValueError(f"duration must be a finite number, got {duration}")
    if sec <= 0:
        raise AudioValueError(f"duration must be positive, got {duration}")
    return sec
