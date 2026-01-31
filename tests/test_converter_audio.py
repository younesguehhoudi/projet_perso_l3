import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
import shutil

import pytest

from converter import convertir_audio, ConversionError


def _ffmpeg_disponible() -> bool:
    return shutil.which("ffmpeg") is not None or shutil.which("avconv") is not None


def _generer_wav(path: Path, duree_ms: int = 500, freq: int = 440, rate: int = 44100) -> None:
    nb_echantillons = int(rate * (duree_ms / 1000))
    amplitude = 32767
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        for i in range(nb_echantillons):
            valeur = int(amplitude * math.sin(2 * math.pi * freq * i / rate))
            wav_file.writeframes(struct.pack("<h", valeur))


def _ffmpeg_cmd() -> str:
    return shutil.which("ffmpeg") or shutil.which("avconv")


@pytest.mark.skipif(not _ffmpeg_disponible(), reason="FFmpeg non disponible")
def test_mp3_vers_wav():
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "tone.wav"
        mp3_path = Path(tmpdir) / "tone.mp3"
        _generer_wav(wav_path)

        cmd = [_ffmpeg_cmd(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), str(mp3_path)]
        subprocess.run(cmd, check=True)

        octets_mp3 = mp3_path.read_bytes()
        octets_wav = convertir_audio(octets_mp3, "mp3", "wav")

        assert octets_wav[:4] == b"RIFF"
        assert b"WAVE" in octets_wav[:16]


@pytest.mark.skipif(not _ffmpeg_disponible(), reason="FFmpeg non disponible")
def test_mp4_vers_mp3():
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "tone.wav"
        mp4_path = Path(tmpdir) / "tone.mp4"
        _generer_wav(wav_path)

        cmd = [_ffmpeg_cmd(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), str(mp4_path)]
        subprocess.run(cmd, check=True)

        octets_mp4 = mp4_path.read_bytes()
        octets_mp3 = convertir_audio(octets_mp4, "mp4", "mp3")

        assert octets_mp3[:3] == b"ID3" or octets_mp3[:2] == b"\xff\xfb"


def test_format_audio_non_supporte():
    with pytest.raises(ConversionError):
        convertir_audio(b"data", "wav", "mp3")
