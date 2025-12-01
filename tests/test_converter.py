import json

import pytest

from converter import convertir_donnees, ConversionError


def test_json_vers_yaml():
    src = '{"name":"Alice","age":30}'
    sortie = convertir_donnees(src, "yaml")
    assert "name:" in sortie and "Alice" in sortie


def test_yaml_vers_json():
    src = """
    name: Bob
    age: 25
    """
    sortie = convertir_donnees(src, "json")
    analyse = json.loads(sortie)
    assert analyse == {"name": "Bob", "age": 25}


def test_reformatage_json():
    src = '{"a":1,"b":2}'
    sortie = convertir_donnees(src, "json")
    # Doit être du JSON valide et joliment formaté (contient espaces/sauts de ligne)
    assert json.loads(sortie) == {"a": 1, "b": 2}
    assert "\n" in sortie


def test_entree_invalide():
    with pytest.raises(ConversionError):
        convertir_donnees("not: [valid", "json")
