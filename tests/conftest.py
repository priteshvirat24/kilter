"""
tests/conftest.py — pytest configuration and shared fixtures.
"""

import os

import pytest

# Set KILTER_FIXTURES=1 for all tests — no DB or live servers required
os.environ.setdefault("KILTER_FIXTURES", "1")
os.environ.setdefault("DATABASE_URL", "postgresql://kilter:kilter@localhost:5432/kilter")
os.environ.setdefault("OPENAI_API_KEY", "test_key_placeholder")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_tests_only")
