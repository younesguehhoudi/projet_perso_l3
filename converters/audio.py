"""Convertisseur pour audio."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from converters.base import BaseConverter
from models import ConversionResult, ConversionError


class AudioConverter(BaseConverter):
    """Convertit entre formats audio (MP3, WAV, etc.)."""
    
    SUPPORTED_CONVERSIONS = {
        ("mp4", "mp3"),
        ("mp3", "wav"),
    }
    
    MIMETYPE_MAP = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mp4": "audio/mp4",
    }
    
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si la conversion est supportée."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        return (source, target) in self.SUPPORTED_CONVERSIONS
    
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        **kwargs
    ) -> ConversionResult:
        """Convertir audio vers un autre format."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        
        if not self.supports(source, target):
            raise ConversionError(f"Format non supporté: {source} → {target}")
        
        ffmpeg = self._get_ffmpeg()
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Créer fichiers temporaires
                input_path = Path(tmpdir) / f"input.{source}"
                output_path = Path(tmpdir) / f"output.{target}"
                
                input_path.write_bytes(input_bytes)
                
                # Exécuter FFmpeg
                cmd = [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", str(input_path),
                    str(output_path),
                ]
                subprocess.run(cmd, check=True)
                
                # Lire le résultat
                output_bytes = output_path.read_bytes()
                
                return ConversionResult(
                    output_bytes=output_bytes,
                    output_format=target,
                    mimetype=self.MIMETYPE_MAP.get(target, "audio/mp3")
                )
        except subprocess.CalledProcessError as e:
            raise ConversionError("Échec de la conversion audio via FFmpeg.") from e
        except Exception as e:
            raise ConversionError(f"Échec de la conversion audio: {str(e)}") from e
    
    @staticmethod
    def _get_ffmpeg() -> str:
        """Obtenir le chemin de FFmpeg."""
        ffmpeg = shutil.which("ffmpeg") or shutil.which("avconv")
        if not ffmpeg:
            raise ConversionError("FFmpeg est requis pour les conversions audio. Installez 'ffmpeg'.")
        return ffmpeg
