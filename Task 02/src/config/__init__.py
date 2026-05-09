"""
Configuration package for the Multi-Agent Chat System.

Re-exports settings so consumers can do: from config import MODEL, OPENAI_API_KEY
"""

from config.settings import MODEL

__all__ = ["MODEL"]
