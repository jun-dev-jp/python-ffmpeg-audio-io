"""Example script demonstrating usage of decoder and FLACEncoder."""

from __future__ import annotations

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.flac import (
    FLACEncoder,
    FLACEncoderCompressionLevel,
)
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError
from python_ffmpeg_audio_io.pcm import PCMCodec


def main() -> None:
    sample_path = Path("samples/sample.mp3")
    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Decoding sample file: {sample_path} ===")
    try:
        pcm = decode(sample_path, PCMCodec.PCM_F32LE)
        print("Successfully decoded!")
        print(f"  - Sample Rate: {pcm.sample_rate.value} Hz ({pcm.sample_rate.name})")
        print(f"  - Channels: {pcm.channels.value} ({pcm.channels.name})")
        print(f"  - Data Size: {len(pcm.data)} bytes")
    except PyFFmpegAudioIOError as e:
        print(f"Failed to decode sample file: {e}")
        return

    print("\n=== Encoding to FLAC with Various Compression Levels ===")

    for level in [
        FLACEncoderCompressionLevel.Level_0,
        FLACEncoderCompressionLevel.Level_5,
        FLACEncoderCompressionLevel.Level_8,
        FLACEncoderCompressionLevel.Level_12,
    ]:
        out_path = output_dir / f"demo_flac_encoder_level_{level.value}.flac"
        encoder = FLACEncoder(compression_level=level)
        try:
            encoder(pcm, out_path, overwrite=True)
            size_kb = out_path.stat().st_size / 1024
            print(
                f"Successfully encoded: {out_path.name} "
                f"(level={level.value}, size={size_kb:.1f} KB)"
            )
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # Also test with S16LE PCM input
    print("\n--- Testing FLAC with 16-bit PCM input ---")
    try:
        pcm_s16 = decode(sample_path, PCMCodec.PCM_S16LE)
        out_s16 = output_dir / "demo_flac_encoder_s16.flac"
        encoder = FLACEncoder(compression_level=FLACEncoderCompressionLevel.Level_5)
        encoder(pcm_s16, out_s16, overwrite=True)
        size_kb = out_s16.stat().st_size / 1024
        print(f"Successfully encoded: {out_s16.name} (size={size_kb:.1f} KB)")
    except PyFFmpegAudioIOError as e:
        print(f"Failed encoding: {e}")

    print(f"\nAll FLAC files successfully generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
