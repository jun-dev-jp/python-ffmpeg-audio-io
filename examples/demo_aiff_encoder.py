"""Example script demonstrating usage of decoder and AIFFEncoder."""

from __future__ import annotations

from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.aiff import AIFFEncoder
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
        pcm = decode(sample_path)
        print("Successfully decoded!")
        print(f"  - Sample Rate: {pcm.sample_rate.value} Hz ({pcm.sample_rate.name})")
        print(f"  - Channels: {pcm.channels.value} ({pcm.channels.name})")
        print(f"  - Data Size: {len(pcm.data)} bytes")
    except PyFFmpegAudioIOError as e:
        print(f"Failed to decode sample file: {e}")
        return

    print("\n=== Encoding to AIFF with Various Codecs ===")

    for codec in [PCMCodec.PCM_S16BE, PCMCodec.PCM_S24BE, PCMCodec.PCM_F32BE]:
        out_path = output_dir / f"demo_aiff_encoder_{codec.value}.aiff"
        encoder = AIFFEncoder(codec=codec)
        try:
            encoder(pcm, out_path, overwrite=True)
            print(f"Successfully encoded: {out_path.name} (codec={codec.value})")
        except PyFFmpegAudioIOError as e:
            print(f"Failed encoding {out_path.name}: {e}")

    print(f"\nAll AIFF files successfully generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
