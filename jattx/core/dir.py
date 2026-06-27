"""jattx/core/dir.py"""
import os


def ensure_dirs():
    for d in ("downloads", "cache", "assets", "jattx/cookies"):
        os.makedirs(d, exist_ok=True)
