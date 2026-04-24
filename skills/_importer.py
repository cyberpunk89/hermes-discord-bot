"""
Centralized import configuration for all skill scripts.
Import this at the top of any script to auto-configure sys.path.
"""
import sys
import os

# Get the project root (parent of skills/)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "game-price", "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "common-games", "scripts"))
