import json

import pytest

from converter import convert_data, ConversionError


def test_json_to_yaml():
    src = '{"name":"Alice","age":30}'
    out = convert_data(src, "yaml")
    assert "name:" in out and "Alice" in out


def test_yaml_to_json():
    src = """
    name: Bob
    age: 25
    """
    out = convert_data(src, "json")
    parsed = json.loads(out)
    assert parsed == {"name": "Bob", "age": 25}


def test_json_reformat():
    src = '{"a":1,"b":2}'
    out = convert_data(src, "json")
    # It should be valid JSON and pretty-printed (contains spaces/newlines)
    assert json.loads(out) == {"a": 1, "b": 2}
    assert "\n" in out


def test_invalid_input():
    with pytest.raises(ConversionError):
        convert_data("not: [valid", "json")
