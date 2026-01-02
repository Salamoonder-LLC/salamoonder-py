# salamoonder/utils/__init__.py
"""Utility classes for working with various anti-bot solutions."""

from .akamai import AkamaiWeb, AkamaiSBSD
from .datadome import Datadome

__all__ = ['AkamaiWeb', 'AkamaiSBSD', 'Datadome']