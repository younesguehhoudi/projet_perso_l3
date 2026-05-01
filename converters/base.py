"""Base abstraite pour les convertisseurs."""

from abc import ABC, abstractmethod
from models import ConversionResult, ConversionError


class BaseConverter(ABC):
    """Classe abstraite pour tous les convertisseurs."""
    
    @abstractmethod
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si cette conversion est supportée.
        
        Args:
            source_format: Format source (ex: 'png')
            target_format: Format cible (ex: 'jpg')
            
        Returns:
            True si supporté
        """
        pass
    
    @abstractmethod
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        **kwargs
    ) -> ConversionResult:
        """Convertir un fichier.
        
        Args:
            input_bytes: Octets du fichier d'entrée
            source_format: Format source
            target_format: Format cible
            **kwargs: Arguments supplémentaires spécifiques
            
        Returns:
            ConversionResult avec les octets convertis
            
        Raises:
            ConversionError: En cas d'erreur
        """
        pass
