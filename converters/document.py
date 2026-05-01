"""Convertisseur pour documents."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from converters.base import BaseConverter
from models import ConversionResult, ConversionError


class DocumentConverter(BaseConverter):
    """Convertit entre formats document (PDF, DOCX, TXT)."""
    
    SUPPORTED_FORMATS = {"pdf", "docx", "txt"}
    
    MIMETYPE_MAP = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si la conversion est supportée."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        return source in self.SUPPORTED_FORMATS and target in self.SUPPORTED_FORMATS and source != target
    
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        txt_encoding: str = "utf-8",
        **kwargs
    ) -> ConversionResult:
        """Convertir document vers un autre format."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        
        if not self.supports(source, target):
            raise ConversionError(f"Format non supporté: {source} → {target}")
        
        if txt_encoding.lower().strip() not in {"utf-8", "latin-1"}:
            raise ConversionError("Encodage TXT non supporté. Utilisez utf-8 ou latin-1.")
        
        libreoffice = self._get_libreoffice()
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                input_path = tmp_path / f"input.{source}"
                
                # Écrire le fichier d'entrée
                if source == "txt":
                    text = input_bytes.decode(txt_encoding)
                    input_path.write_text(text, encoding=txt_encoding)
                else:
                    input_path.write_bytes(input_bytes)
                
                # Exécuter LibreOffice
                cmd = [
                    libreoffice,
                    "--headless",
                    "--convert-to", target,
                    "--outdir", str(tmp_path),
                    str(input_path),
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Lire le fichier de sortie
                output_path = tmp_path / f"input.{target}"
                if not output_path.exists():
                    raise ConversionError("LibreOffice n'a pas produit de fichier de sortie.")
                
                output_bytes = output_path.read_bytes()
                
                return ConversionResult(
                    output_bytes=output_bytes,
                    output_format=target,
                    mimetype=self.MIMETYPE_MAP.get(target, "application/octet-stream")
                )
        except subprocess.CalledProcessError as e:
            raise ConversionError("Échec de la conversion document via LibreOffice.") from e
        except UnicodeDecodeError as e:
            raise ConversionError("Encodage TXT invalide pour le fichier source.") from e
        except Exception as e:
            raise ConversionError(f"Échec de la conversion document: {str(e)}") from e
    
    @staticmethod
    def _get_libreoffice() -> str:
        """Obtenir le chemin de LibreOffice."""
        libreoffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not libreoffice:
            raise ConversionError("LibreOffice est requis pour les conversions de documents. Installez 'libreoffice'.")
        return libreoffice
