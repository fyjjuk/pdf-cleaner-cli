"""Fetcher modules - Document discovery layer."""
from .base import BaseFetcher, FetchedDocument
from .local import LocalFileFetcher

__all__ = ["BaseFetcher", "FetchedDocument", "LocalFileFetcher"]
