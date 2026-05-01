"""Utilitaires du projet."""

import os
from pathlib import Path
from datetime import datetime, timezone

import config


def now_iso() -> str:
    """Retourner l'heure actuelle en ISO format."""
    return datetime.now(timezone.utc).isoformat()


def delete_file(path_str: str) -> None:
    """Supprimer un fichier de manière sécurisée."""
    if not path_str:
        return
    try:
        Path(path_str).unlink(missing_ok=True)
    except Exception:
        pass


def get_file_size(file_obj) -> int:
    """Obtenir la taille d'un fichier FileStorage."""
    stream = getattr(file_obj, "stream", None)
    if stream is None:
        return 0
    position = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(position)
    return size


def get_total_upload_size(files: list) -> int:
    """Calculer la taille totale d'une liste de fichiers."""
    total = 0
    for fichier in files:
        total += get_file_size(fichier)
    return total


def normalize_image_format(fmt: str) -> str:
    """Normaliser le format d'image (jpeg → jpg)."""
    return "jpg" if fmt in {"jpg", "jpeg"} else fmt


def validate_mime_type(conversion_type: str, extension: str, mimetype_input: str) -> None:
    """Valider le type MIME d'un fichier.
    
    Raises:
        ConversionError: Si le MIME ne correspond pas
    """
    from models import ConversionError
    
    expected_mimes = config.MIME_ATTENDUS_PAR_TYPE.get(conversion_type, {}).get(extension, set())
    mime = (mimetype_input or "").lower().split(";")[0].strip()

    if not mime or mime == "application/octet-stream" or not expected_mimes:
        return
    if mime not in expected_mimes:
        raise ConversionError("Le type MIME du fichier ne correspond pas à l'extension.")


def validate_conversion_request(conversion_type: str, target_format: str) -> None:
    """Valider une demande de conversion.
    
    Raises:
        ConversionError: Si invalide
    """
    from models import ConversionError
    
    if conversion_type not in config.FORMATS_CIBLES_AUTORISES:
        raise ConversionError("Type de conversion invalide.")

    if target_format not in config.FORMATS_CIBLES_AUTORISES[conversion_type]:
        raise ConversionError("Format cible invalide pour ce type de conversion.")


def generate_preview(file_path: Path, max_chars: int = 500) -> dict:
    """Générer un aperçu d'un fichier.
    
    Args:
        file_path: Chemin du fichier
        max_chars: Nombre max de caractères pour le texte
        
    Returns:
        Dictionnaire contenant l'aperçu
    """
    import base64
    
    if not file_path.exists():
        return {"error": "Fichier non trouvé."}
    
    ext = file_path.suffix.lower()
    
    try:
        # Aperçu image
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            with open(file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                    ".svg": "image/svg+xml",
                }
                return {
                    "type": "image",
                    "data": f"data:{mime_map.get(ext, 'image/png')};base64,{data}",
                    "size": file_path.stat().st_size
                }
        
        # Aperçu texte
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                contenu = f.read(max_chars)
                return {
                    "type": "text",
                    "data": contenu,
                    "truncated": len(f.read()) > 0,
                    "size": file_path.stat().st_size
                }
        except UnicodeDecodeError:
            return {
                "type": "binary",
                "data": f"Fichier binaire ({file_path.stat().st_size} bytes)",
                "size": file_path.stat().st_size
            }
    except Exception as e:
        return {"error": f"Impossible de prévisualiser: {str(e)}"}
