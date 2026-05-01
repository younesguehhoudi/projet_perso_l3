"""Conteneur unique des instances de services partagées."""

from services.job_service import JobService
from services.history_service import HistoryService
from services.profile_service import ProfileService
from services.conversion_service import ConversionService

# Instances uniques et partagées pour toute l'application
job_service = JobService()
history_service = HistoryService()
profile_service = ProfileService()
conversion_service = ConversionService()

__all__ = ["job_service", "history_service", "profile_service", "conversion_service"]