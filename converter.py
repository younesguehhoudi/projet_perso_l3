import json
import shutil
import subprocess
import tempfile
from typing import Any
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image


class ConversionError(Exception):
    """Levée lorsque la conversion entre formats échoue."""


def _analyser_entree(texte: str) -> tuple[str, Any]:
    """
    Essaie d'analyser l'entrée comme JSON d'abord (strict), puis YAML.
    Retourne un tuple de (format_source, donnees).
    format_source est soit 'json' soit 'yaml'.
    """
    # Essayer JSON d'abord
    try:
        donnees = json.loads(texte)
        return "json", donnees
    except Exception:
        pass

    # Puis YAML (JSON est un sous-ensemble de YAML, donc l'ordre compte)
    try:
        donnees = yaml.safe_load(texte)
        return "yaml", donnees
    except Exception as e:
        raise ConversionError("Impossible de parser le contenu en JSON ou YAML.") from e


def convertir_donnees(texte: str, format_cible: str) -> str:
    """
    Convertit le texte donné (JSON ou YAML) vers le format cible ('json' ou 'yaml').
    Si l'entrée est déjà dans le format cible, elle sera reformatée proprement.
    """
    cible = format_cible.lower().strip()
    if cible not in {"json", "yaml"}:
        raise ConversionError("Format de sortie non supporté. Utilisez 'json' ou 'yaml'.")

    source, donnees = _analyser_entree(texte)

    try:
        if cible == "json":
            # Reformater JSON (ou convertir YAML→JSON)
            return json.dumps(donnees, indent=2, ensure_ascii=False) + "\n"
        else:  # cible == "yaml"
            # YAML formaté sans trier les clés pour préserver l'ordre utilisateur
            return yaml.safe_dump(donnees, sort_keys=False, allow_unicode=True)
    except TypeError as e:
        # Certains types YAML peuvent ne pas être sérialisables en JSON
        raise ConversionError("Les données contiennent des types non sérialisables en JSON.") from e


def convertir_image(octets_entree: bytes, format_source: str, format_cible: str) -> bytes:
    """
    Convertit une image du format_source vers le format_cible.
    Conversions supportées :
    - PNG → JPG
    - JPG → WebP
    - WebP → JPG
    - PNG → WebP
    
    Args:
        octets_entree: Octets bruts de l'image d'entrée
        format_source: Format source (png, jpg, jpeg, webp)
        format_cible: Format cible (png, jpg, jpeg, webp)
    
    Returns:
        bytes: Image convertie en octets
    
    Raises:
        ConversionError: Si la conversion échoue ou le format n'est pas supporté
    """
    source = format_source.lower().strip()
    cible = format_cible.lower().strip()
    
    # Normaliser jpeg en jpg
    if source == "jpeg":
        source = "jpg"
    if cible == "jpeg":
        cible = "jpg"
    
    formats_supportes = {"png", "jpg", "webp"}
    if source not in formats_supportes or cible not in formats_supportes:
        raise ConversionError(f"Format non supporté. Formats acceptés: {', '.join(formats_supportes)}")
    
    try:
        # Charger l'image depuis les octets
        img = Image.open(BytesIO(octets_entree))
        
        # Convertir RGBA en RGB si la cible est JPG (JPG ne supporte pas la transparence)
        if cible == "jpg" and img.mode in ("RGBA", "LA", "P"):
            # Créer un fond blanc
            img_rgb = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            img_rgb.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = img_rgb
        
        # Sauvegarder en octets avec le format approprié
        sortie = BytesIO()
        kwargs_sauvegarde = {}
        
        if cible == "jpg":
            kwargs_sauvegarde["quality"] = 85
            kwargs_sauvegarde["optimize"] = True
            img.save(sortie, format="JPEG", **kwargs_sauvegarde)
        elif cible == "webp":
            kwargs_sauvegarde["quality"] = 85
            kwargs_sauvegarde["method"] = 6  # Meilleure compression
            img.save(sortie, format="WEBP", **kwargs_sauvegarde)
        elif cible == "png":
            kwargs_sauvegarde["optimize"] = True
            img.save(sortie, format="PNG", **kwargs_sauvegarde)
        
        return sortie.getvalue()
        
    except Exception as e:
        raise ConversionError(f"Échec de la conversion d'image: {str(e)}") from e


def convertir_svg_vers_png(octets_entree: bytes) -> bytes:
    """
    Convertit une image SVG en PNG.

    Args:
        octets_entree: Octets bruts du fichier SVG

    Returns:
        bytes: Image PNG convertie

    Raises:
        ConversionError: Si la conversion échoue ou si CairoSVG est absent
    """
    try:
        import cairosvg
    except ImportError as e:
        raise ConversionError("CairoSVG est requis pour convertir un SVG en PNG. Installez le paquet 'CairoSVG'.") from e

    try:
        # Laisser la transparence intacte, convertir aux dimensions natives du SVG
        return cairosvg.svg2png(bytestring=octets_entree)
    except Exception as e:
        raise ConversionError(f"Échec de la conversion SVG → PNG: {str(e)}") from e


def _verifier_libreoffice() -> str:
    libreoffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not libreoffice:
        raise ConversionError(
            "LibreOffice est requis pour les conversions de documents. Installez 'libreoffice' sur votre système."
        )
    return libreoffice


def convertir_document(
    octets_entree: bytes,
    format_source: str,
    format_cible: str,
    txt_encoding: str = "utf-8",
) -> bytes:
    """
    Convertit des documents entre PDF/DOCX/TXT via LibreOffice headless.

    Conversions supportées :
    - PDF ⇄ DOCX
    - PDF ⇄ TXT
    - DOCX ⇄ TXT
    - DOCX ⇄ PDF
    - TXT ⇄ PDF

    Args:
        octets_entree: Octets bruts du document d'entrée
        format_source: Format source (pdf, docx, txt)
        format_cible: Format cible (pdf, docx, txt)
        txt_encoding: Encodage pour les fichiers TXT (defaut: utf-8)

    Returns:
        bytes: Document converti en octets

    Raises:
        ConversionError: Si la conversion echoue ou le format n'est pas supporte
    """
    source = format_source.lower().strip()
    cible = format_cible.lower().strip()

    formats_supportes = {"pdf", "docx", "txt"}
    if source not in formats_supportes or cible not in formats_supportes:
        raise ConversionError("Format document non supporte. Utilisez PDF, DOCX ou TXT.")

    if source == cible:
        raise ConversionError("Le format source et le format cible sont identiques.")

    if txt_encoding.lower().strip() not in {"utf-8", "latin-1"}:
        raise ConversionError("Encodage TXT non supporte. Utilisez utf-8 ou latin-1.")

    libreoffice = _verifier_libreoffice()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            chemin_entree = tmp_dir / f"input.{source}"

            if source == "txt":
                texte = octets_entree.decode(txt_encoding)
                chemin_entree.write_text(texte, encoding=txt_encoding)
            else:
                chemin_entree.write_bytes(octets_entree)

            cmd = [
                libreoffice,
                "--headless",
                "--convert-to",
                cible,
                "--outdir",
                str(tmp_dir),
                str(chemin_entree),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            chemin_sortie = tmp_dir / f"input.{cible}"
            if not chemin_sortie.exists():
                raise ConversionError("LibreOffice n'a pas produit de fichier de sortie.")

            return chemin_sortie.read_bytes()
    except subprocess.CalledProcessError as e:
        raise ConversionError("Echec de la conversion document via LibreOffice.") from e
    except UnicodeDecodeError as e:
        raise ConversionError("Encodage TXT invalide pour le fichier source.") from e
    except Exception as e:
        raise ConversionError(f"Echec de la conversion document: {str(e)}") from e


def _verifier_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg") or shutil.which("avconv")
    if not ffmpeg:
        raise ConversionError("FFmpeg est requis pour les conversions audio. Installez 'ffmpeg' sur votre système.")
    return ffmpeg


def convertir_audio(octets_entree: bytes, format_source: str, format_cible: str) -> bytes:
    """
    Convertit un fichier audio entre formats supportés.
    Conversions supportées :
    - MP4 → MP3
    - MP3 → WAV

    Args:
        octets_entree: Octets bruts de l'audio d'entrée
        format_source: Format source (mp4, mp3)
        format_cible: Format cible (mp3, wav)

    Returns:
        bytes: Audio converti en octets

    Raises:
        ConversionError: Si la conversion échoue ou le format n'est pas supporté
    """
    source = format_source.lower().strip()
    cible = format_cible.lower().strip()

    formats_source = {"mp4", "mp3"}
    formats_cible = {"mp3", "wav"}
    if source not in formats_source or cible not in formats_cible:
        raise ConversionError("Format audio non supporté. Utilisez MP4/MP3 vers MP3/WAV.")

    if source == "mp4" and cible != "mp3":
        raise ConversionError("La conversion MP4 supportée est uniquement MP4 → MP3.")
    if source == "mp3" and cible != "wav":
        raise ConversionError("La conversion MP3 supportée est uniquement MP3 → WAV.")

    ffmpeg = _verifier_ffmpeg()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            entree_path = tempfile.NamedTemporaryFile(delete=False, dir=tmpdir, suffix=f".{source}")
            sortie_path = tempfile.NamedTemporaryFile(delete=False, dir=tmpdir, suffix=f".{cible}")
            entree_path.write(octets_entree)
            entree_path.close()
            sortie_path.close()

            cmd = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                entree_path.name,
                sortie_path.name,
            ]
            subprocess.run(cmd, check=True)

            with open(sortie_path.name, "rb") as f:
                return f.read()
    except subprocess.CalledProcessError as e:
        raise ConversionError("Échec de la conversion audio via FFmpeg.") from e
    except Exception as e:
        raise ConversionError(f"Échec de la conversion audio: {str(e)}") from e
