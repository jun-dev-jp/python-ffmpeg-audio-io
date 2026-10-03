"""Example script demonstrating usage of decode with samples/sample.mp3."""

from pathlib import Path

from python_ffmpeg_audio_io import PCMChannels, PCMSampleRate, decode
from python_ffmpeg_audio_io.exceptions import (
    FFmpegError,
    FileReadError,
    PyFFmpegAudioIOError,
)


def main() -> None:
    sample_path = Path("samples/sample.mp3")
    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    print(f"Decoding sample file to PCM F32LE: {sample_path}\n")

    try:
        pcm = decode(sample_path)
        print("Successfully decoded audio!")
        print(f"  - Sample Rate: {pcm.sample_rate.value} Hz ({pcm.sample_rate.name})")
        print(f"  - Channels: {pcm.channels.value} ({pcm.channels.name})")
        print(f"  - Format: {pcm.format.value} ({pcm.format.name})")
        print(f"  - Decoded Data Size: {len(pcm.data)} bytes")

        # Decode with resampling, stereo conversion, seeking and trimming
        print("\nDecoding with resampling (16kHz), stereo upmixing, and 2-second cut:")
        pcm_converted = decode(
            sample_path,
            sample_rate=PCMSampleRate.RATE_16K,
            channels=PCMChannels.STEREO,
            start_time=1.0,
            duration=2.0,
        )
        print(f"  - Sample Rate: {pcm_converted.sample_rate.value} Hz")
        print(f"  - Channels: {pcm_converted.channels.value}")
        print(f"  - Decoded Data Size: {len(pcm_converted.data)} bytes")
    except (FileReadError, FFmpegError, PyFFmpegAudioIOError) as e:
        print(f"Error decoding audio: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
