"""Service de gestion des jobs."""

import uuid
from threading import Lock
from models import Job, ConversionError
import config
import utils


class JobService:
    """Gère les jobs de conversion."""
    
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._job_order: list[str] = []
        self._lock = Lock()
    
    def create_job(self, conversion_type: str, target_format: str, files_count: int) -> str:
        """Créer un nouveau job.
        
        Returns:
            ID du job créé
        """
        job_id = uuid.uuid4().hex
        job = Job(
            id=job_id,
            type=conversion_type,
            target_format=target_format,
            files_count=files_count,
            status="en_attente",
            created_at=utils.now_iso(),
            updated_at=utils.now_iso(),
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._job_order.append(job_id)
            
            # Nettoyer les anciens jobs si limite dépassée
            while len(self._job_order) > config.MAX_JOBS_MEMOIRE:
                old_id = self._job_order.pop(0)
                old_job = self._jobs.pop(old_id, None)
                if old_job and old_job.api_output_path:
                    utils.delete_file(old_job.api_output_path)
        
        return job_id
    
    def update_job(self, job_id: str, **kwargs) -> None:
        """Mettre à jour un job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = utils.now_iso()
    
    def get_job(self, job_id: str) -> Job | None:
        """Obtenir un job."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_recent_jobs(self, limit: int = 30) -> list[Job]:
        """Obtenir les jobs récents.
        
        Args:
            limit: Nombre de jobs à retourner
            
        Returns:
            Liste des jobs
        """
        with self._lock:
            job_ids = list(reversed(self._job_order[-limit:]))
            return [self._jobs[jid] for jid in job_ids if jid in self._jobs]
    
    def delete_job_output(self, job_id: str) -> None:
        """Supprimer le fichier de sortie d'un job."""
        job = self.get_job(job_id)
        if job and job.api_output_path:
            utils.delete_file(job.api_output_path)
