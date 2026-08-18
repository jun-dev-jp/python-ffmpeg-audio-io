"""Example script demonstrating usage of decoder and AACEncoder."""

from __future__ import annotations

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
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

    print("\n=== Encoding to AAC with Various Settings ===")

    # 1. Test different CBR bitrates
    print("\n--- Testing CBR (Constant Bitrate) ---")
    for bitrate in [
        AACEncoderBitrate.Kbps_64,
        AACEncoderBitrate.Kbps_128,
    ]:
        out_path = output_dir / f"demo_aac_encoder_cbr_{bitrate.value}.m4a"
        encoder = AACEncoder(bitrate=bitrate, mode=AACEncoderMode.CBR)
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 2. Test ABR (Average Bitrate)
    print("\n--- Testing ABR (Average Bitrate) ---")
    for bitrate in [AACEncoderBitrate.Kbps_64, AACEncoderBitrate.Kbps_128]:
        out_path = output_dir / f"demo_aac_encoder_abr_{bitrate.value}.m4a"
        encoder = AACEncoder(bitrate=bitrate, mode=AACEncoderMode.ABR)
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 3. Test VBR (Variable Bitrate) with different quality levels
    print("\n--- Testing VBR (Variable Bitrate) ---")
    for quality in [
        AACEncoderQualityLevel.Quality_0,
        AACEncoderQualityLevel.Quality_2,
        AACEncoderQualityLevel.Quality_5,
    ]:
        out_path = output_dir / f"demo_aac_encoder_vbr_q{quality.value}.m4a"
        encoder = AACEncoder(quality=quality, mode=AACEncoderMode.VBR)
        try:
            encoder(pcm, out_path, overwrite=True)
            msg = f"quality=q{quality.value}, 5=best, 0=worst"
            print(f"Successfully encoded: {out_path.name} ({msg})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    print(f"\nAll AAC files successfully generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
