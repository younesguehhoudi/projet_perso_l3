"""Service d'orchestration des conversions."""

from pathlib import Path
import uuid
import zipfile
from werkzeug.datastructures import FileStorage

from models import ConversionError
import config
import utils
import converters


class ConversionService:
    """Orchestre les conversions de fichiers."""
    
    def convert_file(
        self,
        conversion_type: str,
        target_format: str,
        original_filename: str,
        input_bytes: bytes,
        mimetype_input: str = "",
        txt_encoding: str = "utf-8",
    ) -> tuple[bytes, str, str]:
        """Convertir un fichier unique.
        
        Args:
            conversion_type: Type de conversion
            target_format: Format cible
            original_filename: Nom du fichier original
            input_bytes: Octets d'entrée
            mimetype_input: Type MIME d'entrée
            txt_encoding: Encodage pour TXT
            
        Returns:
            Tuple (output_bytes, output_format, mimetype)
            
        Raises:
            ConversionError: En cas d'erreur
        """
        # Extraire extension source
        ext_source = Path(original_filename).suffix.lower().lstrip(".")
        if not ext_source:
            raise ConversionError("Impossible de détecter le format du fichier.")
        
        # Valider MIME
        utils.validate_mime_type(conversion_type, ext_source, mimetype_input)
        
        # Traiter selon le type de conversion
        if conversion_type == "image":
            return self._convert_image(ext_source, target_format, input_bytes)
        elif conversion_type == "audio":
            return self._convert_audio(ext_source, target_format, input_bytes)
        elif conversion_type == "document":
            return self._convert_document(ext_source, target_format, input_bytes, txt_encoding)
        elif conversion_type == "data":
            return self._convert_data(ext_source, target_format, input_bytes)
        else:
            raise ConversionError(f"Type de conversion inconnu: {conversion_type}")
    
    def _convert_image(self, source_ext: str, target_format: str, input_bytes: bytes) -> tuple[bytes, str, str]:
        """Convertir une image."""
        source_fmt = utils.normalize_image_format(source_ext)
        target_fmt = utils.normalize_image_format(target_format)
        
        if source_fmt == target_fmt and source_ext != "svg":
            raise ConversionError(f"L'image est déjà au format {target_format.upper()}.")
        
        if target_format not in {"png", "jpg", "jpeg", "webp", "pdf"}:
            raise ConversionError("Format de sortie invalide pour les images (PNG, JPG, WebP, PDF).")
        
        converter = converters.get_converter("image", source_fmt, target_fmt)
        result = converter.convert(input_bytes, source_fmt, target_fmt)
        
        return result.output_bytes, result.output_format, result.mimetype
    
    def _convert_audio(self, source_ext: str, target_format: str, input_bytes: bytes) -> tuple[bytes, str, str]:
        """Convertir un fichier audio."""
        if source_ext not in {"mp4", "mp3"}:
            raise ConversionError("Format audio source non supporté (MP4 ou MP3).")
        
        if target_format not in {"mp3", "wav"}:
            raise ConversionError("Format de sortie invalide pour l'audio (MP3 ou WAV).")
        
        if source_ext == target_format:
            raise ConversionError(f"Le fichier est déjà au format {target_format.upper()}.")
        
        # Validations de conversion supportée
        if source_ext == "mp4" and target_format != "mp3":
            raise ConversionError("Pour les MP4, seul le format MP3 est supporté.")
        if source_ext == "mp3" and target_format != "wav":
            raise ConversionError("Pour les MP3, seul le format WAV est supporté.")
        
        converter = converters.get_converter("audio", source_ext, target_format)
        result = converter.convert(input_bytes, source_ext, target_format)
        
        return result.output_bytes, result.output_format, result.mimetype
    
    def _convert_document(
        self,
        source_ext: str,
        target_format: str,
        input_bytes: bytes,
        txt_encoding: str,
    ) -> tuple[bytes, str, str]:
        """Convertir un document."""
        formats_docs = {"pdf", "docx", "txt"}
        
        if source_ext not in formats_docs:
            raise ConversionError("Format document source non supporté (PDF, DOCX ou TXT).")
        if target_format not in formats_docs:
            raise ConversionError("Format de sortie invalide pour les documents (PDF, DOCX ou TXT).")
        if source_ext == target_format:
            raise ConversionError(f"Le fichier est déjà au format {target_format.upper()}.")
        
        converter = converters.get_converter("document", source_ext, target_format)
        result = converter.convert(input_bytes, source_ext, target_format, txt_encoding=txt_encoding)
        
        return result.output_bytes, result.output_format, result.mimetype
    
    def _convert_data(self, source_ext: str, target_format: str, input_bytes: bytes) -> tuple[bytes, str, str]:
        """Convertir des données (JSON/YAML)."""
        if target_format not in {"json", "yaml"}:
            raise ConversionError("Format de sortie invalide (JSON ou YAML).")
        
        if source_ext not in {"json", "yaml", "yml", "txt", "conf"}:
            raise ConversionError("Format de fichier source non supporté pour les données.")
        
        # Normaliser l'extension source
        source_fmt = "json" if source_ext == "json" else "yaml"
        
        if source_fmt == target_format:
            raise ConversionError(f"Le fichier est déjà au format {target_format.upper()}.")
        
        try:
            text = input_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ConversionError("Le fichier doit être un texte UTF-8 (JSON/YAML).") from e
        
        converter = converters.get_converter("data", source_fmt, target_format)
        result = converter.convert(text.encode("utf-8"), source_fmt, target_format)
        
        return result.output_bytes, result.output_format, result.mimetype
