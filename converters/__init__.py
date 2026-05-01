"""Convertisseurs disponibles."""

from converters.base import BaseConverter
from converters.data import DataConverter
from converters.image import ImageConverter, SVGConverter
from converters.audio import AudioConverter
from converters.document import DocumentConverter
from models import ConversionError, ConversionResult

__all__ = [
    "BaseConverter",
    "DataConverter",
    "ImageConverter",
    "SVGConverter",
    "AudioConverter",
    "DocumentConverter",
    "get_converter",
]


def get_converter(conversion_type: str, source_format: str, target_format: str) -> BaseConverter:
    """Obtenir le convertisseur approprié.
    
    Args:
        conversion_type: Type de conversion (data, image, audio, document)
        source_format: Format source
        target_format: Format cible
        
    Returns:
        Instance du convertisseur
        
    Raises:
        ConversionError: Si pas de convertisseur trouvé
    """
    source = source_format.lower().strip()
    target = target_format.lower().strip()
    
    converters = []
    
    if conversion_type == "data":
        converters = [DataConverter()]
    elif conversion_type == "image":
        converters = [SVGConverter(), ImageConverter()]
    elif conversion_type == "audio":
        converters = [AudioConverter()]
    elif conversion_type == "document":
        converters = [DocumentConverter()]
    else:
        raise ConversionError(f"Type de conversion inconnu: {conversion_type}")
    
    for converter in converters:
        if converter.supports(source, target):
            return converter
    
    raise ConversionError(f"Conversion non supportée: {source} → {target}")
