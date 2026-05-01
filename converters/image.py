"""Convertisseur pour images."""

from io import BytesIO
from PIL import Image
from converters.base import BaseConverter
from models import ConversionResult, ConversionError


class ImageConverter(BaseConverter):
    """Convertit entre formats d'image (PNG, JPG, WebP)."""
    
    SUPPORTED_FORMATS = {"png", "jpg", "webp", "pdf"}
    
    MIMETYPE_MAP = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "pdf": "application/pdf",
    }
    
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si la conversion est supportée."""
        source = source_format.lower().strip()
        source = "jpg" if source == "jpeg" else source
        target = target_format.lower().strip()
        target = "jpg" if target == "jpeg" else target
        return source in self.SUPPORTED_FORMATS and target in self.SUPPORTED_FORMATS
    
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        **kwargs
    ) -> ConversionResult:
        """Convertir image vers un autre format."""
        source = source_format.lower().strip()
        source = "jpg" if source == "jpeg" else source
        target = target_format.lower().strip()
        target = "jpg" if target == "jpeg" else target
        
        if not self.supports(source, target):
            raise ConversionError(f"Format non supporté: {source} → {target}")
        
        try:
            # Charger l'image
            img = Image.open(BytesIO(input_bytes))
            
            # Gérer la transparence pour JPG
            if target == "jpg" and img.mode in ("RGBA", "LA", "P"):
                img_rgb = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                img_rgb.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = img_rgb
            
            # Sauvegarder en octets
            output = BytesIO()
            save_kwargs = {}
            
            if target == "jpg":
                save_kwargs["quality"] = 85
                save_kwargs["optimize"] = True
                img.save(output, format="JPEG", **save_kwargs)
            elif target == "webp":
                save_kwargs["quality"] = 85
                save_kwargs["method"] = 6
                img.save(output, format="WEBP", **save_kwargs)
            elif target == "png":
                save_kwargs["optimize"] = True
                img.save(output, format="PNG", **save_kwargs)
            elif target == "pdf":
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(output, format="PDF")
            
            return ConversionResult(
                output_bytes=output.getvalue(),
                output_format=target,
                mimetype=self.MIMETYPE_MAP.get(target, "image/png")
            )
        except Exception as e:
            raise ConversionError(f"Échec de la conversion d'image: {str(e)}") from e


class SVGConverter(BaseConverter):
    """Convertit SVG en PNG."""
    
    def supports(self, source_format: str, target_format: str) -> bool:
        """Vérifier si la conversion est supportée."""
        return source_format.lower().strip() == "svg" and target_format.lower().strip() == "png"
    
    def convert(
        self,
        input_bytes: bytes,
        source_format: str,
        target_format: str,
        **kwargs
    ) -> ConversionResult:
        """Convertir SVG en PNG."""
        try:
            import cairosvg
        except ImportError as e:
            raise ConversionError("CairoSVG est requis pour convertir SVG. Installez 'cairosvg'.") from e
        
        try:
            output = cairosvg.svg2png(bytestring=input_bytes)
            return ConversionResult(
                output_bytes=output,
                output_format="png",
                mimetype="image/png"
            )
        except Exception as e:
            raise ConversionError(f"Échec de la conversion SVG → PNG: {str(e)}") from e
