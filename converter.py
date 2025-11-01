import json
from typing import Any

import yaml


class ConversionError(Exception):
    """Raised when conversion between formats fails."""


def _parse_input(text: str) -> tuple[str, Any]:
    """
    Try to parse the input as JSON first (strict), then YAML.
    Returns a tuple of (source_format, data).
    source_format is either 'json' or 'yaml'.
    """
    # Try JSON first
    try:
        data = json.loads(text)
        return "json", data
    except Exception:
        pass

    # Then YAML (JSON is a subset of YAML, so ordering matters)
    try:
        data = yaml.safe_load(text)
        return "yaml", data
    except Exception as e:
        raise ConversionError("Impossible de parser le contenu en JSON ou YAML.") from e


def convert_data(text: str, target_format: str) -> str:
    """
    Convert the given text (JSON or YAML) into the target format ('json' or 'yaml').
    If input is already in the target format, it will be reformatted nicely.
    """
    target = target_format.lower().strip()
    if target not in {"json", "yaml"}:
        raise ConversionError("Format de sortie non supporté. Utilisez 'json' ou 'yaml'.")

    source, data = _parse_input(text)

    try:
        if target == "json":
            # Reformat JSON (or convert YAML->JSON)
            return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        else:  # target == "yaml"
            # Pretty YAML without sorting keys to keep user order when possible
            return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    except TypeError as e:
        # Some YAML types may not be JSON serializable; provide a clearer error
        raise ConversionError("Les données contiennent des types non sérialisables en JSON.") from e
