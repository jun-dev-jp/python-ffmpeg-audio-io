"""Example script demonstrating usage of decoder and OpusEncoder."""

from __future__ import annotations

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.opus import (
    OpusEncoder,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
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

    print("\n=== Encoding to Opus with Various Settings ===")

    # 1. Test VBR with various bitrates (.opus)
    print("\n--- Testing VBR (Variable Bitrate) ---")
    for bitrate in [
        OpusEncoderBitrate.Kbps_64,
        OpusEncoderBitrate.Kbps_128,
        OpusEncoderBitrate.Kbps_256,
    ]:
        out_path = output_dir / f"demo_opus_encoder_vbr_{bitrate.value}.opus"
        encoder = OpusEncoder(
            bitrate=bitrate,
            mode=OpusEncoderMode.VBR,
            application=OpusEncoderApplication.AUDIO,
        )
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 2. Test CBR (.ogg)
    print("\n--- Testing CBR (Constant Bitrate) ---")
    for bitrate in [OpusEncoderBitrate.Kbps_64, OpusEncoderBitrate.Kbps_128]:
        out_path = output_dir / f"demo_opus_encoder_cbr_{bitrate.value}.ogg"
        encoder = OpusEncoder(
            bitrate=bitrate,
            mode=OpusEncoderMode.CBR,
            application=OpusEncoderApplication.AUDIO,
        )
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (bitrate={bitrate.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    # 3. Test CVBR and Application types
    print("\n--- Testing CVBR and Applications ---")
    for app in [
        OpusEncoderApplication.VOIP,
        OpusEncoderApplication.LOW_DELAY,
    ]:
        out_path = output_dir / f"demo_opus_encoder_cvbr_{app.value}.opus"
        encoder = OpusEncoder(
            bitrate=OpusEncoderBitrate.Kbps_96,
            mode=OpusEncoderMode.CVBR,
            application=app,
        )
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (application={app.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    print(f"\nAll Opus files successfully generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
