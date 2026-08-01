"""Example script demonstrating usage of decoder and SimpleMP3Encoder with samples/sample.mp3."""

from __future__ import annotations

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode_to_PCM_F32LE_with_ffmpeg
from python_ffmpeg_audio_io.encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from python_ffmpeg_audio_io.exceptions import FFmpegError
from python_ffmpeg_audio_io.pcm import PCMFormat


def main() -> None:
    sample_path = Path("samples/sample.mp3")
    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Decoding sample file: {sample_path} ===")
    try:
        pcm_data, sample_rate, channels = decode_to_PCM_F32LE_with_ffmpeg(sample_path)
        print("Successfully decoded!")
        print(f"  - Sample Rate: {sample_rate.value} Hz ({sample_rate.name})")
        print(f"  - Channels: {channels.value} ({channels.name})")
        print(f"  - Data Size: {len(pcm_data)} bytes")
    except FFmpegError as e:
        print(f"Failed to decode sample file: {e}")
        return

    pcm_format = PCMFormat.F32LE

    print("\n=== Encoding to MP3 with Various Settings ===")

    # 1. Test different CBR bitrates
    print("\n--- Testing CBR (Constant Bitrate) ---")
    for bitrate in [
        MP3EncoderBitrate.Kbps_64,
        MP3EncoderBitrate.Kbps_128,
    ]:
        out_path = output_dir / f"demo_mp3_encoder_cbr_{bitrate.value}.mp3"
        encoder = MP3Encoder(bitrate=bitrate, mode=MP3EncoderMode.CBR)
        try:
            encoder(
                pcm_data, pcm_format, sample_rate, channels, out_path, overwrite=True
            )
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except FFmpegError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 2. Test ABR (Average Bitrate)
    print("\n--- Testing ABR (Average Bitrate) ---")
    for bitrate in [MP3EncoderBitrate.Kbps_64, MP3EncoderBitrate.Kbps_128]:
        out_path = output_dir / f"demo_mp3_encoder_abr_{bitrate.value}.mp3"
        encoder = MP3Encoder(bitrate=bitrate, mode=MP3EncoderMode.ABR)
        try:
            encoder(
                pcm_data, pcm_format, sample_rate, channels, out_path, overwrite=True
            )
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except FFmpegError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 3. Test VBR (Variable Bitrate) with different quality levels
    print("\n--- Testing VBR (Variable Bitrate) ---")
    for quality in [
        MP3EncoderQualityLevel.Quality_0,
        MP3EncoderQualityLevel.Quality_2,
        MP3EncoderQualityLevel.Quality_9,
    ]:
        out_path = output_dir / f"demo_mp3_encoder_vbr_q{quality.value}.mp3"
        encoder = MP3Encoder(quality=quality, mode=MP3EncoderMode.VBR)
        try:
            encoder(
                pcm_data, pcm_format, sample_rate, channels, out_path, overwrite=True
            )
            print(
                f"Successfully encoded: {out_path.name} (quality=q{quality.value}, 0=best, 9=worst)"
            )
        except FFmpegError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    print(f"\nAll MP3 files successfully generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
