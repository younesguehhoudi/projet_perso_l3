import shutil

import pytest

from converter import convertir_document, ConversionError


def _libreoffice_disponible() -> bool:
    return shutil.which("soffice") is not None or shutil.which("libreoffice") is not None


@pytest.mark.skipif(not _libreoffice_disponible(), reason="LibreOffice non disponible")
def test_txt_vers_docx():
    contenu = "Bonjour document"
    octets_docx = convertir_document(contenu.encode("utf-8"), "txt", "docx")

    assert octets_docx[:2] == b"PK"


@pytest.mark.skipif(not _libreoffice_disponible(), reason="LibreOffice non disponible")
def test_txt_vers_pdf():
    contenu = "Bonjour PDF"
    octets_pdf = convertir_document(contenu.encode("utf-8"), "txt", "pdf")

    assert octets_pdf[:4] == b"%PDF"


def test_format_document_non_supporte():
    with pytest.raises(ConversionError):
        convertir_document(b"data", "rtf", "pdf")
