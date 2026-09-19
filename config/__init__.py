"""
Smart Task Manager configuration package.
Exposes the Celery app instance when Django starts.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
