"""
Comprehensive unit tests for Chakma Corpus Engine.
"""

from pathlib import Path
import pytest

from generator.corpus_engine import CorpusEngine
from generator.charset_engine import CharsetEngine


def test_corpus_loading():
    engine = CorpusEngine()
    assert len(engine.sentences) > 0
    assert len(engine.vocabulary) > 0
    assert engine.sentences[0] == "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁"


def test_empty_lines_and_comments(tmp_path: Path):
    sentences_file = tmp_path / "test_sentences.txt"
    sentences_file.write_text(
        "# This is a comment\n\n\n𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴\n   \n# Another comment\n𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴\n\n",
        encoding="utf-8"
    )

    vocab_file = tmp_path / "test_vocab.txt"
    vocab_file.write_text("# Vocab\n𑄟𑄚𑄪𑄌𑄴\n\n𑄢𑄎\n", encoding="utf-8")

    engine = CorpusEngine(
        sentences_path=sentences_file,
        vocabulary_path=vocab_file,
    )

    assert len(engine.sentences) == 2
    assert engine.sentences[0] == "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴"
    assert engine.sentences[1] == "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴"
    assert len(engine.vocabulary) == 2


def test_text_normalization():
    # Multiple whitespace and tab collapsing
    raw = "   𑄟𑄚𑄪𑄌𑄴     𑄃𑄟𑄢𑄴 \t\t 𑄘𑄬𑄌𑄴   "
    normalized = CorpusEngine.normalize_text(raw)
    assert normalized == "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴"


def test_deterministic_random_selection_reproducibility():
    engine1 = CorpusEngine(seed=123)
    engine2 = CorpusEngine(seed=123)

    sample1 = engine1.get_random_sentences(5)
    sample2 = engine2.get_random_sentences(5)
    assert sample1 == sample2

    word1 = engine1.get_random_words(10)
    word2 = engine2.get_random_words(10)
    assert word1 == word2


def test_seed_override_reproducibility():
    engine = CorpusEngine(seed=42)

    # Calling with explicit seed should always be identical
    s1 = engine.get_random_sentence(seed=999)
    s2 = engine.get_random_sentence(seed=999)
    assert s1 == s2

    w1 = engine.get_random_word(seed=777)
    w2 = engine.get_random_word(seed=777)
    assert w1 == w2


def test_supported_and_unsupported_characters():
    engine = CorpusEngine()
    supported = engine.get_supported_characters()
    unsupported = engine.get_unsupported_characters()

    assert len(supported) > 0
    assert len(unsupported) == 0, f"Authentic sample corpus should have 0 unsupported characters, found: {unsupported}"

    report = engine.validate()
    assert report.is_valid is True
    assert report.unsupported_characters_count == 0
    assert len(report.errors) == 0


def test_unsupported_character_detection(tmp_path: Path):
    bad_sentences = tmp_path / "bad_sentences.txt"
    bad_sentences.write_text(
        "𑄟𑄚𑄪𑄌𑄴 Hello 123 𑄘𑄬𑄌𑄴\n",
        encoding="utf-8"
    )

    bad_vocab = tmp_path / "bad_vocab.txt"
    bad_vocab.write_text("𑄟𑄚𑄪𑄌𑄴\nXYZ\n", encoding="utf-8")

    engine = CorpusEngine(
        sentences_path=bad_sentences,
        vocabulary_path=bad_vocab,
    )

    unsupported = engine.get_unsupported_characters()
    assert len(unsupported) > 0
    assert "H" in unsupported
    assert "e" in unsupported
    assert "X" in unsupported

    report = engine.validate()
    assert report.is_valid is False
    assert report.unsupported_characters_count > 0
    assert any("Found" in e for e in report.errors)


def test_empty_corpus_error_handling(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    engine = CorpusEngine(
        sentences_path=empty_file,
        vocabulary_path=empty_file,
    )

    with pytest.raises(ValueError, match="no sentences"):
        engine.get_random_sentence()

    with pytest.raises(ValueError, match="no vocabulary"):
        engine.get_random_word()
