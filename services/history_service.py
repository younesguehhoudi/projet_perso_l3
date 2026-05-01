"""Service de gestion de l'historique."""

import json
import uuid
from threading import Lock
from pathlib import Path
from models import HistoryEntry, ConversionError
import config
import utils


class HistoryService:
    """Gère l'historique des conversions."""
    
    def __init__(self):
        self._lock = Lock()
    
    def add_entry(
        self,
        job_id: str,
        conversion_type: str,
        target_format: str,
        source_formats: set[str],
        total_size: int,
        files_count: int,
        success_count: int,
        error_count: int,
        status: str,
    ) -> HistoryEntry:
        """Ajouter une entrée à l'historique."""
        entry = HistoryEntry(
            id=uuid.uuid4().hex,
            job_id=job_id,
            date=utils.now_iso(),
            type=conversion_type,
            source_formats=sorted(source_formats),
            target_format=target_format,
            size_bytes=total_size,
            files_count=files_count,
            success_count=success_count,
            error_count=error_count,
            status=status,
        )
        
        with self._lock:
            history = self._load()
            history.append(entry.to_dict())
            
            # Limiter la taille de l'historique
            if len(history) > config.MAX_HISTORY_ENTRIES:
                history = history[-config.MAX_HISTORY_ENTRIES:]
            
            self._save(history)
        
        return entry
    
    def get_recent(self, limit: int = 20) -> list[dict]:
        """Obtenir les entrées récentes.
        
        Args:
            limit: Nombre d'entrées (max: MAX_API_HISTORY_RETURNS)
            
        Returns:
            Liste des entrées
        """
        limit = max(1, min(limit, config.MAX_API_HISTORY_RETURNS))
        
        with self._lock:
            history = self._load()
        
        # Retourner dans l'ordre inverse (plus récent en premier)
        return list(reversed(history[-limit:]))
    
    def _load(self) -> list[dict]:
        """Charger l'historique depuis le fichier."""
        if not config.HISTORIQUE_PATH.exists():
            return []
        
        try:
            data = json.loads(config.HISTORIQUE_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
    
    def _save(self, history: list[dict]) -> None:
        """Sauvegarder l'historique dans le fichier."""
        config.HISTORIQUE_PATH.write_text(
            json.dumps(history, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
