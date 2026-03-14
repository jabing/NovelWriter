#!/usr/bin/env python3
"""
Novel Agent System - AI-powered novel writing and publishing system.

This system uses multiple specialized AI agents to:
- Plan and structure novels
- Create consistent characters and worlds
- Write chapters in various genres (Sci-Fi, Fantasy, Romance, History, Military)
- Edit and maintain consistency
- Publish to multiple platforms automatically
"""

from pathlib import Path

# Version
__version__ = "0.1.0"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = DATA_DIR / "config"
NOVELS_DIR = DATA_DIR / "novels"
OPENVIKING_DIR = DATA_DIR / "openviking"
