"""
NLP Engines package for Presidio Desktop Redactor.

This package contains custom NLP engine implementations for different frameworks:
- FlairNlpEngine: Flair framework integration
- StanzaNlpEngine: Stanza framework integration  
- EngineFactory: Factory pattern for creating engines
"""

from .engine_factory import NlpEngineFactory

__all__ = ['NlpEngineFactory']