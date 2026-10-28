"""Example script demonstrating usage of run_ffprobe and get_audio_info."""

from pathlib import Path

from python_ffmpeg_audio_io.exceptions import (
    FFmpegError,
    FileReadError,
    PyFFmpegAudioIOError,
)
from python_ffmpeg_audio_io.ffprobe import (
    get_audio_info,
    run_ffprobe,
)


def main() -> None:
    sample_path = Path("samples/65_BPM93.mp3")
    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    print(f"Inspecting sample file: {sample_path}\n")

    import json

    # 1. Using run_ffprobe
    print("--- 1. run_ffprobe output (raw JSON dict) ---")
    try:
        raw_data = run_ffprobe(sample_path)
        print(json.dumps(raw_data, indent=2, ensure_ascii=False))
    except (FileReadError, FFmpegError) as e:
        print(f"Error running run_ffprobe: {e}")

    print("\n--- 2. get_audio_info output (AudioInfo dataclass) ---")
    try:
        info = get_audio_info(sample_path)
        print(f"  - Sample Rate: {info.sample_rate} Hz")
        print(f"  - Channels: {info.channels}")
        print(f"  - Duration: {info.duration:.2f} s")
        print(f"  - Codec Name: {info.codec_name}")
        print(f"  - Format Name: {info.format_name}")
        print(f"  - Format Long Name: {info.format_long_name}")
        print(f"  - Size: {info.size} bytes")
        print(f"  - Bit Rate: {info.bit_rate} bps")
    except (FileReadError, FFmpegError, PyFFmpegAudioIOError) as e:
        print(f"Error getting audio info: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
