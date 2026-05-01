"""Service de gestion des profils de conversion."""

import json
import uuid
from threading import Lock
from pathlib import Path
from models import Profile
import config


class ProfileService:
    """Gère les profils de conversion."""
    
    def __init__(self):
        self._lock = Lock()
    
    def load_all(self) -> dict[str, list[dict]]:
        """Charger tous les profils."""
        if not config.PROFILS_PATH.exists():
            return config.PROFILS_PAR_DEFAUT
        
        try:
            data = json.loads(config.PROFILS_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else config.PROFILS_PAR_DEFAUT
        except Exception:
            return config.PROFILS_PAR_DEFAUT
    
    def get_profiles(self, conversion_type: str | None = None) -> dict[str, list[dict]] | list[dict]:
        """Obtenir les profils.
        
        Args:
            conversion_type: Type spécifique ou None pour tous
            
        Returns:
            Profils filtrés ou tous les profils
        """
        with self._lock:
            all_profiles = self.load_all()
            
            if conversion_type is None:
                return all_profiles
            
            return all_profiles.get(conversion_type, [])
    
    def add_profile(
        self,
        conversion_type: str,
        name: str,
        source: str,
        target: str,
    ) -> dict:
        """Ajouter un profil.
        
        Returns:
            Le profil créé
        """
        profile_id = f"{source}2{target}_{uuid.uuid4().hex[:6]}"
        new_profile = {
            "id": profile_id,
            "name": name,
            "source": source,
            "target": target,
        }
        
        with self._lock:
            profiles = self.load_all()
            if conversion_type not in profiles:
                profiles[conversion_type] = []
            
            profiles[conversion_type].append(new_profile)
            self._save(profiles)
        
        return new_profile
    
    def delete_profile(self, conversion_type: str, profile_id: str) -> bool:
        """Supprimer un profil.
        
        Returns:
            True si supprimé, False si non trouvé
        """
        with self._lock:
            profiles = self.load_all()
            if conversion_type in profiles:
                original_len = len(profiles[conversion_type])
                profiles[conversion_type] = [
                    p for p in profiles[conversion_type] if p["id"] != profile_id
                ]
                
                if len(profiles[conversion_type]) < original_len:
                    self._save(profiles)
                    return True
        
        return False
    
    def _save(self, profiles: dict[str, list[dict]]) -> None:
        """Sauvegarder les profils."""
        config.PROFILS_PATH.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
