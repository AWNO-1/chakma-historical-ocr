"""
Tests for Corpus Engine.
"""

import pytest
from generator.corpus_engine import CorpusEngine


def test_corpus_engine_init():
    engine = CorpusEngine()
    assert engine.sentences_path.exists()
    assert engine.vocabulary_path.exists()
    assert isinstance(engine.sentences, list)
    assert isinstance(engine.vocabulary, list)


def test_corpus_sample():
    engine = CorpusEngine()
    line = engine.sample_line()
    assert isinstance(line, str)
    para = engine.sample_paragraph(num_lines=3)
    assert isinstance(para, list)
    assert len(para) == 3
