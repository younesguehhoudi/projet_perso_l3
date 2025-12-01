import io
from PIL import Image
import pytest

from converter import convertir_image, ConversionError


def creer_image_test(format: str, mode: str = "RGB", taille: tuple = (100, 100)) -> bytes:
    """Fonction auxiliaire pour créer une image test en mémoire."""
    img = Image.new(mode, taille, color=(255, 0, 0))  # Image rouge
    sortie = io.BytesIO()
    
    if format.lower() == "jpg":
        img.save(sortie, format="JPEG", quality=85)
    elif format.lower() == "png":
        img.save(sortie, format="PNG")
    elif format.lower() == "webp":
        img.save(sortie, format="WEBP", quality=85)
    
    return sortie.getvalue()


def test_png_vers_jpg():
    """Test conversion PNG vers JPG."""
    octets_png = creer_image_test("png")
    octets_jpg = convertir_image(octets_png, "png", "jpg")
    
    # Vérifier que la sortie est un JPG valide
    img = Image.open(io.BytesIO(octets_jpg))
    assert img.format == "JPEG"
    assert img.size == (100, 100)


def test_jpg_vers_webp():
    """Test conversion JPG vers WebP."""
    octets_jpg = creer_image_test("jpg")
    octets_webp = convertir_image(octets_jpg, "jpg", "webp")
    
    # Vérifier que la sortie est un WebP valide
    img = Image.open(io.BytesIO(octets_webp))
    assert img.format == "WEBP"
    assert img.size == (100, 100)


def test_webp_vers_jpg():
    """Test conversion WebP vers JPG."""
    octets_webp = creer_image_test("webp")
    octets_jpg = convertir_image(octets_webp, "webp", "jpg")
    
    # Vérifier que la sortie est un JPG valide
    img = Image.open(io.BytesIO(octets_jpg))
    assert img.format == "JPEG"
    assert img.size == (100, 100)


def test_png_vers_webp():
    """Test conversion PNG vers WebP."""
    octets_png = creer_image_test("png")
    octets_webp = convertir_image(octets_png, "png", "webp")
    
    # Vérifier que la sortie est un WebP valide
    img = Image.open(io.BytesIO(octets_webp))
    assert img.format == "WEBP"
    assert img.size == (100, 100)


def test_png_avec_transparence_vers_jpg():
    """Test conversion PNG avec transparence (RGBA) vers JPG."""
    # Créer une image RGBA avec transparence
    octets_png = creer_image_test("png", mode="RGBA")
    octets_jpg = convertir_image(octets_png, "png", "jpg")
    
    # Vérifier que la sortie est un JPG valide (transparence convertie en fond blanc)
    img = Image.open(io.BytesIO(octets_jpg))
    assert img.format == "JPEG"
    assert img.mode == "RGB"  # Doit être RGB, pas RGBA


def test_alias_jpeg():
    """Test que 'jpeg' est correctement aliasé vers 'jpg'."""
    octets_jpg = creer_image_test("jpg")
    octets_webp = convertir_image(octets_jpg, "jpeg", "webp")
    
    img = Image.open(io.BytesIO(octets_webp))
    assert img.format == "WEBP"


def test_format_non_supporte():
    """Test que les formats non supportés lèvent ConversionError."""
    octets_png = creer_image_test("png")
    
    with pytest.raises(ConversionError):
        convertir_image(octets_png, "png", "bmp")
    
    with pytest.raises(ConversionError):
        convertir_image(octets_png, "gif", "jpg")


def test_donnees_image_invalides():
    """Test que des données d'image invalides lèvent ConversionError."""
    octets_invalides = b"pas une image"
    
    with pytest.raises(ConversionError):
        convertir_image(octets_invalides, "png", "jpg")
