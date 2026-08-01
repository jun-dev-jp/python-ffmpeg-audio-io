"""Example script demonstrating usage of decode_to_PCM_F32LE_with_ffmpeg with samples/sample.mp3."""

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode_to_PCM_F32LE_with_ffmpeg
from python_ffmpeg_audio_io.exceptions import FFmpegError, PyFFmpegAudioIOError


def main() -> None:
    sample_path = Path("samples/sample.mp3")
    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    print(f"Decoding sample file to PCM F32LE: {sample_path}\n")

    try:
        pcm_data, sample_rate, channels = decode_to_PCM_F32LE_with_ffmpeg(sample_path)
        print("Successfully decoded audio!")
        print(f"  - Sample Rate: {sample_rate.value} Hz ({sample_rate.name})")
        print(f"  - Channels: {channels.value} ({channels.name})")
        print(f"  - Decoded Data Size: {len(pcm_data)} bytes")
    except (FileNotFoundError, FFmpegError, PyFFmpegAudioIOError) as e:
        print(f"Error decoding audio: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
