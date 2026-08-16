"""
Comprehensive unit tests for Chakma Charset Engine and Class Registry.
"""

import json
from pathlib import Path
import pytest

from generator.charset_engine import CharsetEngine, ChakmaClass
from utils.file_utils import get_project_root


def test_charset_loading_and_counts():
    engine = CharsetEngine()
    assert engine.total_classes == 71
    assert engine.num_classes == 71
    assert len(engine.get_all_classes()) == 71


def test_contiguous_and_unique_ids():
    engine = CharsetEngine()
    classes = engine.get_all_classes()

    ids = [c.id for c in classes]
    assert ids == list(range(71)), "Class IDs must be contiguous and 0-indexed from 0 to 70."

    unicodes = [c.unicode for c in classes]
    assert len(set(unicodes)) == 71, "All Unicode code points must be unique."

    chars = [c.character for c in classes]
    assert len(set(chars)) == 71, "All UTF-8 characters must be unique."


def test_category_distribution():
    engine = CharsetEngine()
    report = engine.validate_charset()
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0

    cats = report["categories"]
    assert cats["signs_and_modifiers"] == 5
    assert cats["independent_vowels"] == 4
    assert cats["consonants"] == 34
    assert cats["dependent_vowels"] == 14
    assert cats["digits"] == 10
    assert cats["punctuation"] == 4
    assert sum(cats.values()) == 71


def test_lookups_by_id():
    engine = CharsetEngine()

    # First class: Candrabindu
    c0 = engine.get_class_by_id(0)
    assert c0 is not None
    assert c0.unicode == "U+11100"
    assert c0.name == "CHAKMA SIGN CANDRABINDU"
    assert c0.category == "signs_and_modifiers"

    # Consonant: KAA
    c7 = engine.get_class_by_id(7)
    assert c7 is not None
    assert c7.unicode == "U+11107"
    assert c7.name == "CHAKMA LETTER KAA"
    assert c7.category == "consonants"

    # Last class: VAA
    c70 = engine.get_class_by_id(70)
    assert c70 is not None
    assert c70.unicode == "U+11147"
    assert c70.name == "CHAKMA LETTER VAA"
    assert c70.category == "consonants"

    # Non-existent ID
    assert engine.get_class_by_id(999) is None
    assert engine.get_class_by_id(-1) is None


def test_lookups_by_unicode_and_char():
    engine = CharsetEngine()

    # Lookup by unicode format with or without prefix
    c_aa = engine.get_class_by_unicode("U+11103")
    assert c_aa is not None
    assert c_aa.id == 3
    assert c_aa.name == "CHAKMA LETTER AA"

    c_aa_lower = engine.get_class_by_unicode("11103")
    assert c_aa_lower is not None
    assert c_aa_lower.id == 3

    # Lookup by character
    c_char = engine.get_class_by_char("𑄃")
    assert c_char is not None
    assert c_char.id == 3

    # get_class_id
    assert engine.get_class_id("𑄃") == 3
    assert engine.get_class_id("U+11103") == 3
    assert engine.get_class_id("non_existent") is None


def test_character_validation():
    engine = CharsetEngine()
    assert engine.is_valid_char("𑄃") is True
    assert engine.is_valid_char("A") is False
    assert engine.is_valid_char("𑄇") is True


def test_id_and_character_mappings():
    engine = CharsetEngine()
    id_to_char = engine.get_id_to_char_map()
    assert len(id_to_char) == 71
    assert id_to_char[0] == "𑄀"
    assert id_to_char[7] == "𑄇"

    id_to_name = engine.get_id_to_name_map()
    assert len(id_to_name) == 71
    assert id_to_name[0] == "CHAKMA SIGN CANDRABINDU"


def test_validation_detects_duplicate_ids(tmp_path: Path):
    bad_data = {
        "classes": [
            {"id": 0, "unicode": "U+11100", "character": "𑄀", "name": "A", "category": "consonants"},
            {"id": 0, "unicode": "U+11101", "character": "𑄁", "name": "B", "category": "consonants"},
        ]
    }
    file_path = tmp_path / "bad_charset.json"
    file_path.write_text(json.dumps(bad_data), encoding="utf-8")

    engine = CharsetEngine(charset_path=file_path, config_path=None)
    report = engine.validate_charset()
    assert report["is_valid"] is False
    assert any("Duplicate class IDs detected" in e for e in report["errors"])


def test_validation_detects_missing_contiguous_ids(tmp_path: Path):
    bad_data = {
        "classes": [
            {"id": 0, "unicode": "U+11100", "character": "𑄀", "name": "A", "category": "consonants"},
            {"id": 2, "unicode": "U+11101", "character": "𑄁", "name": "B", "category": "consonants"},
        ]
    }
    file_path = tmp_path / "bad_charset2.json"
    file_path.write_text(json.dumps(bad_data), encoding="utf-8")

    engine = CharsetEngine(charset_path=file_path, config_path=None)
    report = engine.validate_charset()
    assert report["is_valid"] is False
    assert any("Missing contiguous class IDs" in e for e in report["errors"])
