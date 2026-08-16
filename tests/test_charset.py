"""
Tests for Charset Engine and character mapping.
"""

import pytest
from generator.charset_engine import CharsetEngine
from utils.file_utils import get_project_root


def test_charset_engine_init():
    engine = CharsetEngine()
    assert engine.charset_path.exists()
    assert isinstance(engine.num_classes, int)
    assert engine.num_classes >= 0


def test_charset_engine_unknown_char():
    engine = CharsetEngine()
    assert engine.get_class_id("NON_EXISTENT_CHAR") is None
    assert engine.is_valid_char("NON_EXISTENT_CHAR") is False
