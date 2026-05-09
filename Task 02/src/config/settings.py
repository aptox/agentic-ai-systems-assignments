"""
Application settings loaded from environment variables.

Loads .env file via python-dotenv and exposes configuration constants
used throughout the multi-agent system.
"""

import os

from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o-mini"
