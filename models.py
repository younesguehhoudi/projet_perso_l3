"""Modèles de données pour le projet."""

from typing import Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


class ConversionError(Exception):
    """Exception levée lors d'une erreur de conversion."""
    pass


@dataclass
class Job:
    """Représente un travail de conversion."""
    id: str
    type: str
    target_format: str
    files_count: int
    status: str = "en_attente"
    success_count: int = 0
    error_count: int = 0
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    api_output_path: str = ""
    api_output_name: str = ""
    api_output_mimetype: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convertir en dictionnaire."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Job":
        """Créer depuis un dictionnaire."""
        return Job(**{k: v for k, v in data.items() if k in Job.__dataclass_fields__})


@dataclass
class Profile:
    """Représente un profil de conversion."""
    id: str
    name: str
    source: str
    target: str

    def to_dict(self) -> dict[str, Any]:
        """Convertir en dictionnaire."""
        return asdict(self)


@dataclass
class HistoryEntry:
    """Représente une entrée d'historique."""
    id: str
    job_id: str
    date: str
    type: str
    source_formats: list[str]
    target_format: str
    size_bytes: int
    files_count: int
    success_count: int
    error_count: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Convertir en dictionnaire."""
        return asdict(self)


@dataclass
class ConversionResult:
    """Résultat d'une conversion unique."""
    output_bytes: bytes
    output_format: str
    mimetype: str
