"""Base audio stream writer module using FFmpeg."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from collections.abc import Sequence
from os import W_OK, PathLike, access
from pathlib import Path
from types import TracebackType
from typing import Self

from ..exceptions import (
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileWriteError,
    StreamBrokenError,
    StreamClosedError,
)
from ..pcm import PCM, PCMChannels, PCMFormat, PCMSampleRate


class BaseAudioStreamWriter(ABC):
    """Abstract base class for streaming audio encoders using FFmpeg stdin pipe.

    Attributes:
        path: Destination path for the output audio file.
        sample_rate: Sample rate of the incoming PCM audio.
        channels: Channel count of the incoming PCM audio.
        pcm_format: Format of the incoming PCM audio.
        frame_size: Size in bytes of one audio frame.
        frames_written: Total number of audio frames written so far.
        bytes_written: Total number of bytes written so far.
    """

    path: Path
    sample_rate: PCMSampleRate
    channels: PCMChannels
    pcm_format: PCMFormat
    frame_size: int
    frames_written: int
    bytes_written: int

    _process: subprocess.Popen[bytes]
    _closed: bool

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate | int = PCMSampleRate.RATE_44K,
        channels: PCMChannels | int = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
    ) -> None:
        """Initialize BaseAudioStreamWriter and spawn the FFmpeg encoding subprocess.

        Args:
            output_path: Destination path for the output audio file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing destination file (default: False).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False, or
                not writable.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg fails to spawn.
        """
        if isinstance(sample_rate, PCMSampleRate):
            self.sample_rate = sample_rate
        elif isinstance(sample_rate, int) and not isinstance(sample_rate, bool):
            try:
                self.sample_rate = PCMSampleRate(sample_rate)
            except ValueError as e:
                raise AudioValueError(f"Unsupported sample rate: {sample_rate}") from e
        else:
            t_name = type(sample_rate).__name__
            raise AudioTypeError(
                f"sample_rate must be PCMSampleRate or int, got {t_name}"
            )

        if isinstance(channels, PCMChannels):
            self.channels = channels
        elif isinstance(channels, int) and not isinstance(channels, bool):
            try:
                self.channels = PCMChannels(channels)
            except ValueError as e:
                raise AudioValueError(f"Unsupported channel count: {channels}") from e
        else:
            t_name = type(channels).__name__
            raise AudioTypeError(f"channels must be PCMChannels or int, got {t_name}")

        if not isinstance(pcm_format, PCMFormat):
            t_name = type(pcm_format).__name__
            raise AudioTypeError(f"pcm_format must be PCMFormat, got {t_name}")
        self.pcm_format = pcm_format

        dest_path = self._check_output_path(
            output_path, self.supported_formats, overwrite
        )
        self.path = dest_path

        self.frame_size = self.pcm_format.bytes_per_sample * self.channels.value
        self.frames_written = 0
        self.bytes_written = 0
        self._closed = False

        self._process = self._spawn_ffmpeg(overwrite)

    @property
    @abstractmethod
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for this stream writer."""

    @abstractmethod
    def _get_codec_args(self) -> Sequence[str]:
        """Return codec-specific FFmpeg arguments."""

    def _check_output_path(
        self,
        output_path: str | PathLike[str],
        supported_formats: Sequence[str],
        overwrite: bool,
    ) -> Path:
        """Validate and prepare the output destination path.

        Args:
            output_path: The target output file path.
            supported_formats: Sequence of supported file extension names.
            overwrite: Whether existing output files should be overwritten.

        Returns:
            Path: Validated Path object.

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If the file extension is not supported.
            FileWriteError: If output file already exists and overwrite is False,
                or if the existing file is not writable.
        """
        if not isinstance(output_path, (str, PathLike)):
            t_name = type(output_path).__name__
            raise AudioTypeError(f"output_path must be a str or PathLike, got {t_name}")
        if not isinstance(overwrite, bool):
            raise AudioTypeError(
                f"overwrite must be a bool, got {type(overwrite).__name__}"
            )
        if not isinstance(supported_formats, Sequence):
            t_name = type(supported_formats).__name__
            raise AudioTypeError(
                f"supported_formats must be a Sequence of str, got {t_name}"
            )

        path = Path(output_path)
        ext = path.suffix.lower().lstrip(".")
        allowed = [fmt.lower().lstrip(".") for fmt in supported_formats]

        if not ext or ext not in allowed:
            expected = [f".{fmt}" for fmt in allowed]
            msg = (
                f"Unsupported output file extension: '{path.suffix}'. "
                f"Expected one of: {expected}"
            )
            raise AudioValueError(msg)

        if path.exists() and not overwrite:
            raise FileWriteError(f"Output file already exists: {path}")

        if path.exists() and overwrite and not access(path, W_OK):
            raise FileWriteError(f"Output file is not writable: {path}")

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def _spawn_ffmpeg(self, overwrite: bool) -> subprocess.Popen[bytes]:
        """Spawn the FFmpeg subprocess for stream encoding.

        Args:
            overwrite: Whether to overwrite existing destination file.

        Returns:
            subprocess.Popen[bytes]: The spawned FFmpeg subprocess.

        Raises:
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If spawning FFmpeg fails.
        """
        cmd: list[str] = [
            "ffmpeg",
            "-y" if overwrite else "-n",
            "-f",
            self.pcm_format.value,
            "-ar",
            str(self.sample_rate.value),
            "-ac",
            str(self.channels.value),
            "-i",
            "pipe:0",
            *self._get_codec_args(),
            "-loglevel",
            "error",
            str(self.path),
        ]

        try:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            if e.errno == 2:
                raise FFmpegNotFoundError(
                    "ffmpeg executable not found. Please ensure FFmpeg is in PATH."
                ) from e
            raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e

    @property
    def closed(self) -> bool:
        """Return True if the stream writer is closed."""
        return self._closed

    def write_bytes(self, data: bytes | bytearray | memoryview) -> int:
        """Write raw PCM bytes to the encoder stream.

        Args:
            data: Raw PCM byte data. Must be aligned to frame_size.

        Returns:
            int: Number of bytes written.

        Raises:
            StreamClosedError: If the writer is closed.
            AudioTypeError: If data is not bytes-like.
            AudioValueError: If data length is not aligned to frame_size.
            StreamBrokenError: If FFmpeg pipe is broken or process terminates
                unexpectedly.
        """
        if self._closed:
            raise StreamClosedError("Cannot write to a closed audio stream.")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            t_name = type(data).__name__
            raise AudioTypeError(f"data must be bytes-like, got {t_name}")
        if len(data) == 0:
            return 0
        if len(data) % self.frame_size != 0:
            msg = (
                f"Data length ({len(data)} bytes) is not aligned to frame size "
                f"({self.frame_size} bytes = {self.pcm_format.bytes_per_sample} "
                f"bytes/sample * {self.channels.value} channels)."
            )
            raise AudioValueError(msg)

        stdin = self._process.stdin
        if stdin is None:
            raise StreamClosedError("Stream stdin pipe is unavailable.")

        try:
            stdin.write(data)
            stdin.flush()
        except (BrokenPipeError, OSError) as e:
            stderr = ""
            if self._process.stderr is not None:
                try:
                    stderr = (
                        self._process.stderr.read()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                except OSError:
                    pass
            raise StreamBrokenError(
                f"FFmpeg stdin pipe broke: {stderr or e}",
                stderr=stderr,
            ) from e

        # Check if process terminated with error during write
        returncode = self._process.poll()
        if returncode is not None and returncode != 0:
            stderr = ""
            if self._process.stderr is not None:
                try:
                    stderr = (
                        self._process.stderr.read()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                except OSError:
                    pass
            raise StreamBrokenError(
                f"FFmpeg process terminated unexpectedly with code "
                f"{returncode}: {stderr}",
                stderr=stderr,
            )

        n_bytes = len(data)
        self.bytes_written += n_bytes
        self.frames_written += n_bytes // self.frame_size
        return n_bytes

    def write(self, pcm: PCM) -> int:
        """Write a PCM audio chunk to the encoder stream.

        Args:
            pcm: PCM instance containing audio data and format metadata.

        Returns:
            int: Number of audio frames written.

        Raises:
            StreamClosedError: If the writer is closed.
            AudioTypeError: If pcm is not a PCM instance.
            AudioValueError: If PCM format, sample rate, or channels mismatch
                stream config.
            StreamBrokenError: If FFmpeg pipe breaks or process terminates unexpectedly.
        """
        if self._closed:
            raise StreamClosedError("Cannot write to a closed audio stream.")
        if not isinstance(pcm, PCM):
            t_name = type(pcm).__name__
            raise AudioTypeError(f"pcm must be an instance of PCM, got {t_name}")
        if pcm.format != self.pcm_format:
            msg = f"PCM format mismatch: expected {self.pcm_format}, got {pcm.format}"
            raise AudioValueError(msg)
        if pcm.sample_rate != self.sample_rate:
            msg = (
                f"Sample rate mismatch: expected {self.sample_rate}, "
                f"got {pcm.sample_rate}"
            )
            raise AudioValueError(msg)
        if pcm.channels != self.channels:
            msg = (
                f"Channel count mismatch: expected {self.channels}, got {pcm.channels}"
            )
            raise AudioValueError(msg)

        self.write_bytes(pcm.data)
        return len(pcm.data) // self.frame_size

    def flush(self) -> None:
        """Flush pending buffered audio data to the FFmpeg process.

        Raises:
            StreamClosedError: If the writer is closed.
        """
        if self._closed:
            raise StreamClosedError("Cannot flush a closed audio stream.")
        if self._process.stdin is not None:
            try:
                self._process.stdin.flush()
            except OSError:
                pass

    def close(self) -> None:
        """Close the stream writer, finish encoding, and wait for FFmpeg to exit.

        Raises:
            FFmpegError: If FFmpeg process exits with a non-zero status code.
        """
        if self._closed:
            return

        self._closed = True
        stderr_output = ""

        if self._process.stdin is not None:
            try:
                self._process.stdin.close()
            except OSError:
                pass

        try:
            _, stderr_bytes = self._process.communicate(timeout=15.0)
            if stderr_bytes:
                stderr_output = stderr_bytes.decode("utf-8", errors="ignore").strip()
        except subprocess.TimeoutExpired:
            self._process.terminate()
            try:
                _, stderr_bytes = self._process.communicate(timeout=2.0)
                if stderr_bytes:
                    stderr_output = stderr_bytes.decode(
                        "utf-8", errors="ignore"
                    ).strip()
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

        returncode = self._process.returncode
        if returncode is not None and returncode != 0:
            raise FFmpegError(
                f"FFmpeg failed to encode to {self.path} (exit code {returncode}): "
                f"{stderr_output}",
                stderr=stderr_output,
            )

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and close the stream writer."""
        if exc_type is not None:
            if not self._closed:
                self._closed = True
                if self._process.stdin is not None:
                    try:
                        self._process.stdin.close()
                    except OSError:
                        pass
                if self._process.poll() is None:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait()
                if self._process.stderr is not None:
                    try:
                        self._process.stderr.close()
                    except OSError:
                        pass
            return

        self.close()


__all__ = ["BaseAudioStreamWriter"]
