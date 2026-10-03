"""Audio stream reader module using FFmpeg pipe."""

from __future__ import annotations

import subprocess
import threading
from collections import deque
from collections.abc import Iterator
from os import R_OK, PathLike, access
from pathlib import Path
from types import TracebackType

from ._validation import (
    validate_channels_opt,
    validate_duration,
    validate_sample_rate_opt,
    validate_start_time,
)
from .exceptions import (
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    StreamBrokenError,
    StreamClosedError,
)
from .ffprobe import AudioInfo, get_audio_info
from .pcm import PCM, PCMChannels, PCMCodec, PCMFormat, PCMSampleRate


class AudioStreamReader:
    """Stream reader for decoding audio files into raw PCM chunks using FFmpeg.

    Attributes:
        path: Path to the input audio file.
        info: Audio metadata retrieved via FFprobe.
        pcm_codec: The PCM codec used for decoding.
        pcm_format: The PCM format corresponding to pcm_codec.
        sample_rate: Sample rate of the decoded audio.
        channels: Channel count of the decoded audio.
        chunk_frames: Number of audio frames per chunk during iteration.
        frame_size: Size in bytes of one audio frame.
        start_time: Starting offset in seconds for decoding, or None.
        duration: Duration in seconds to decode, or None.
    """

    path: Path
    info: AudioInfo
    pcm_codec: PCMCodec
    pcm_format: PCMFormat
    sample_rate: PCMSampleRate
    channels: PCMChannels
    chunk_frames: int
    frame_size: int
    start_time: float | None
    duration: float | None

    _process: subprocess.Popen[bytes]
    _closed: bool
    _eof: bool
    _stderr_chunks: deque[bytes]
    _stderr_lock: threading.Lock
    _stderr_total_bytes: int
    _stderr_max_bytes: int
    _stderr_thread: threading.Thread | None

    def __init__(
        self,
        path: str | PathLike[str],
        pcm_codec: PCMCodec = PCMCodec.PCM_F32LE,
        chunk_frames: int = 1024,
        sample_rate: PCMSampleRate | None = None,
        channels: PCMChannels | None = None,
        start_time: float | int | str | None = None,
        duration: float | int | str | None = None,
    ) -> None:
        """Initialize AudioStreamReader and spawn the FFmpeg decoding process.

        Args:
            path: Path to the input audio file.
            pcm_codec: The PCM codec to decode into (default: PCM_F32LE).
            chunk_frames: Default frame count per chunk during reading (default: 1024).
            sample_rate: Target sample rate for resampling, or None to keep original
                (default: None).
            channels: Target channels for channel conversion, or None to keep original
                (default: None).
            start_time: Starting offset in seconds or timecode string (e.g. "00:01:30")
                to seek before decoding, or None (default: None).
            duration: Duration in seconds or timecode string (e.g. "00:00:10") of audio
                to decode, or None to decode to end (default: None).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If chunk_frames is not positive, start_time/duration
                are invalid, or sample_rate/channels are unsupported.
            FileReadError: If the audio file does not exist or is unreadable.
            FFmpegNotFoundError: If FFmpeg or FFprobe executable is not in PATH.
            FFmpegError: If FFmpeg fails to start or metadata probe fails.
        """
        if not isinstance(path, (str, PathLike)):
            raise AudioTypeError(
                f"path must be a str or PathLike, got {type(path).__name__}"
            )
        if not isinstance(pcm_codec, PCMCodec):
            t_name = type(pcm_codec).__name__
            raise AudioTypeError(
                f"pcm_codec must be an instance of PCMCodec, got {t_name}"
            )
        if not isinstance(chunk_frames, int) or isinstance(chunk_frames, bool):
            raise AudioTypeError(
                f"chunk_frames must be an int, got {type(chunk_frames).__name__}"
            )
        if chunk_frames <= 0:
            raise AudioValueError(f"chunk_frames must be positive, got {chunk_frames}")

        target_sample_rate = validate_sample_rate_opt(sample_rate)
        target_channels = validate_channels_opt(channels)
        self.start_time = validate_start_time(start_time)
        self.duration = validate_duration(duration)

        audio_path = Path(path)
        if not audio_path.exists():
            raise FileReadError(f"Audio file not found: {audio_path}")
        if not audio_path.is_file():
            raise FileReadError(f"Audio file is not a regular file: {audio_path}")
        if not access(audio_path, R_OK):
            raise FileReadError(f"Audio file is not readable: {audio_path}")

        self.path = audio_path
        self.pcm_codec = pcm_codec
        self.pcm_format = pcm_codec.pcm_format
        self.chunk_frames = chunk_frames

        self.info = get_audio_info(audio_path)

        if target_channels is not None:
            self.channels = target_channels
        else:
            try:
                self.channels = PCMChannels(self.info.channels)
            except ValueError as e:
                msg = (
                    f"Unsupported channel count '{self.info.channels}' "
                    f"in audio file: {audio_path}"
                )
                raise AudioValueError(msg) from e

        if target_sample_rate is not None:
            self.sample_rate = target_sample_rate
        else:
            try:
                self.sample_rate = PCMSampleRate(self.info.sample_rate)
            except ValueError as e:
                msg = (
                    f"Unsupported sample rate '{self.info.sample_rate}' "
                    f"in audio file: {audio_path}"
                )
                raise AudioValueError(msg) from e

        self.frame_size = self.pcm_format.bytes_per_sample * self.channels.value
        self._closed = False
        self._eof = False
        self._stderr_chunks = deque()
        self._stderr_lock = threading.Lock()
        self._stderr_total_bytes = 0
        self._stderr_max_bytes = 64 * 1024
        self._process = self._spawn_ffmpeg()
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            daemon=True,
            name=f"AudioStreamReader-stderr-{id(self)}",
        )
        self._stderr_thread.start()

    def _spawn_ffmpeg(self) -> subprocess.Popen[bytes]:
        """Spawn the FFmpeg subprocess for streaming decode.

        Returns:
            subprocess.Popen[bytes]: The spawned FFmpeg subprocess.

        Raises:
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If spawning FFmpeg fails.
        """
        cmd = ["ffmpeg", "-nostdin"]
        if self.start_time is not None:
            cmd.extend(["-ss", str(self.start_time)])
        cmd.extend(
            [
                "-i",
                str(self.path),
                "-v",
                "error",
            ]
        )
        if self.duration is not None:
            cmd.extend(["-t", str(self.duration)])
        cmd.extend(
            [
                "-f",
                self.pcm_format.value,
                "-acodec",
                self.pcm_codec.value,
                "-ar",
                str(self.sample_rate.value),
                "-ac",
                str(self.channels.value),
                "pipe:1",
            ]
        )

        try:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise FFmpegNotFoundError(
                "ffmpeg executable not found. Please ensure FFmpeg is in PATH."
            ) from e
        except OSError as e:
            raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e

    def _drain_stderr(self) -> None:
        """Continuously read and drain FFmpeg stderr in a background thread."""
        stderr = self._process.stderr
        if stderr is None:
            return

        try:
            while True:
                chunk = stderr.read(4096)
                if not chunk:
                    break
                with self._stderr_lock:
                    self._stderr_chunks.append(chunk)
                    self._stderr_total_bytes += len(chunk)
                    while (
                        self._stderr_total_bytes > self._stderr_max_bytes
                        and self._stderr_chunks
                    ):
                        removed = self._stderr_chunks.popleft()
                        self._stderr_total_bytes -= len(removed)
        except (OSError, ValueError):
            pass
        finally:
            try:
                stderr.close()
            except OSError:
                pass

    def _get_stderr(self) -> str:
        """Return captured stderr output as decoded string."""
        with self._stderr_lock:
            data = b"".join(self._stderr_chunks)
        return data.decode("utf-8", errors="replace").strip()

    def _wait_process(self, timeout: float = 5.0) -> int:
        """Wait for the FFmpeg subprocess to finish and join stderr thread."""
        try:
            returncode = self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.terminate()
            try:
                returncode = self._process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                returncode = self._process.wait()

        if self._stderr_thread is not None and self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=1.0)

        return returncode

    @property
    def closed(self) -> bool:
        """Return True if the reader stream has been closed."""
        return self._closed

    def _read_exact(self, n_bytes: int) -> bytes:
        """Read up to n_bytes from stdout until buffer is filled or EOF."""
        stdout = self._process.stdout
        if stdout is None:
            raise StreamClosedError("Stream stdout pipe is unavailable.")

        buffer = bytearray()
        while len(buffer) < n_bytes:
            chunk = stdout.read(n_bytes - len(buffer))
            if not chunk:
                break
            buffer.extend(chunk)

        return bytes(buffer)

    def read(self, frames: int | None = None) -> PCM | None:
        """Read a chunk of audio frames as a PCM instance.

        Args:
            frames: Number of frames to read. If None, uses chunk_frames.

        Returns:
            PCM | None: Decoded PCM data for this chunk, or None on EOF.

        Raises:
            StreamClosedError: If stream is closed.
            AudioTypeError: If frames is not an int.
            AudioValueError: If frames is non-positive.
            StreamBrokenError: If stream pipe breaks or ends unaligned.
            FFmpegError: If FFmpeg process terminated with error.
        """
        if self._closed:
            raise StreamClosedError("Cannot read from a closed AudioStreamReader.")
        if self._eof:
            return None

        target_frames = self.chunk_frames if frames is None else frames
        if not isinstance(target_frames, int) or isinstance(target_frames, bool):
            raise AudioTypeError(
                f"frames must be an int, got {type(target_frames).__name__}"
            )
        if target_frames <= 0:
            raise AudioValueError(f"frames must be positive, got {target_frames}")

        n_bytes = target_frames * self.frame_size
        try:
            raw_bytes = self._read_exact(n_bytes)
        except (BrokenPipeError, OSError) as e:
            self._eof = True
            self._wait_process()
            stderr = self._get_stderr()
            raise StreamBrokenError(
                f"Failed to read from FFmpeg stdout pipe: {stderr or e}",
                stderr=stderr,
            ) from e

        if not raw_bytes:
            self._eof = True
            returncode = self._wait_process()
            if returncode != 0:
                stderr = self._get_stderr()
                err_msg = (
                    f"FFmpeg process terminated unexpectedly with code "
                    f"{returncode}: {stderr}"
                )
                raise FFmpegError(err_msg, stderr=stderr)
            return None

        if len(raw_bytes) % self.frame_size != 0:
            self._eof = True
            self._wait_process()
            stderr = self._get_stderr()
            raise StreamBrokenError(
                f"Stream ended with unaligned data ({len(raw_bytes)} bytes, "
                f"frame size is {self.frame_size} bytes): {stderr}",
                stderr=stderr,
            )

        return PCM(
            data=raw_bytes,
            format=self.pcm_format,
            sample_rate=self.sample_rate,
            channels=self.channels,
        )

    def read_bytes(self, frames: int | None = None) -> bytes:
        """Read a chunk of audio frames as raw bytes.

        Args:
            frames: Number of frames to read. If None, uses chunk_frames.

        Returns:
            bytes: Raw PCM bytes, or empty bytes on EOF.
        """
        pcm = self.read(frames)
        return bytes(pcm.data) if pcm is not None else b""

    def __iter__(self) -> Iterator[PCM]:
        """Iterate over audio chunks as PCM instances."""
        while not self._closed:
            chunk = self.read()
            if chunk is None:
                break
            yield chunk

    def __enter__(self) -> AudioStreamReader:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and close reader stream."""
        self.close()

    def close(self) -> None:
        """Close the stream reader and terminate FFmpeg subprocess."""
        if self._closed:
            return

        self._closed = True

        if self._process.stdout is not None:
            try:
                self._process.stdout.close()
            except OSError:
                pass

        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

        if self._stderr_thread is not None and self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=1.0)

        if self._process.stderr is not None:
            try:
                self._process.stderr.close()
            except OSError:
                pass


__all__ = ["AudioStreamReader"]
