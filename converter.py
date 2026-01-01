import json
from typing import Any
from io import BytesIO

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
