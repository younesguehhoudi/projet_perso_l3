"""Convertisseur pour données (JSON/YAML)."""

import json
import yaml
from converters.base import BaseConverter
from models import ConversionResult, ConversionError


class DataConverter(BaseConverter):
    """Convertit entre JSON et YAML."""
    
    SUPPORTED_FORMATS = {"json", "yaml"}
    
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si la conversion est supportée."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        return source in self.SUPPORTED_FORMATS and target in self.SUPPORTED_FORMATS
    
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        **kwargs
    ) -> ConversionResult:
        """Convertir données entre JSON et YAML."""
        source = source_format.lower().strip()
        target = target_format.lower().strip()
        
        if not self.supports(source, target):
            raise ConversionError(f"Format non supporté: {source} → {target}")
        
        # Parser l'entrée
        text = input_bytes.decode("utf-8")
        data = self._parse_input(text)
        
        # Convertir vers le format cible
        if target == "json":
            output = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        else:  # yaml
            output = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        
        return ConversionResult(
            output_bytes=output.encode("utf-8"),
            output_format=target,
            mimetype="application/json" if target == "json" else "application/x-yaml"
        )
    
    @staticmethod
    def _parse_input(text: str) -> dict:
        """Parser JSON ou YAML depuis du texte.
        
        Raises:
            ConversionError: Si parsing impossible
        """
        # Essayer JSON en premier
        try:
            return json.loads(text)
        except Exception:
            pass
        
        # Essayer YAML
        try:
            return yaml.safe_load(text)
        except Exception as e:
            raise ConversionError("Impossible de parser le contenu en JSON ou YAML.") from e
