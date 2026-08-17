"""
Authoritative Corpus Engine for Chakma Historical OCR.
Manages sentence corpora, vocabulary pools, text normalization, character validation,
and deterministic reproducible sampling for the synthetic data generator.
"""

from collections import Counter
from dataclasses import dataclass, field
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import unicodedata

from generator.charset_engine import CharsetEngine
from utils.file_utils import resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("corpus_engine")


@dataclass
class CorpusValidationReport:
    """Detailed summary of corpus validation results."""
    is_valid: bool
    total_sentences: int
    total_words: int
    unique_characters_count: int
    supported_characters_count: int
    unsupported_characters_count: int
    unsupported_characters: List[str] = field(default_factory=list)
    character_frequencies: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_sentences": self.total_sentences,
            "total_words": self.total_words,
            "unique_characters_count": self.unique_characters_count,
            "supported_characters_count": self.supported_characters_count,
            "unsupported_characters_count": self.unsupported_characters_count,
            "unsupported_characters": self.unsupported_characters,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class CorpusEngine:
    """
    Linguistic text management and sampling engine for synthetic manuscript generation.
    """

    def __init__(
        self,
        sentences_path: Union[str, Path] = "corpus/sentences.txt",
        vocabulary_path: Union[str, Path] = "corpus/vocabulary.txt",
        charset_engine: Optional[Union[CharsetEngine, str, Path]] = None,
        seed: int = 42,
    ):
        self.sentences_path = resolve_path(sentences_path)
        self.vocabulary_path = resolve_path(vocabulary_path)
        self.seed = seed
        self._rng = random.Random(self.seed)

        if charset_engine is None:
            self.charset_engine = CharsetEngine()
        elif isinstance(charset_engine, (str, Path)):
            self.charset_engine = CharsetEngine(charset_path=charset_engine)
        else:
            self.charset_engine = charset_engine

        self._sentences: List[str] = []
        self._vocabulary: List[str] = []
        self._all_corpus_chars: Set[str] = set()

        self.load()

    def set_seed(self, seed: int) -> None:
        """Update deterministic RNG seed."""
        self.seed = seed
        self._rng = random.Random(seed)

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text to Unicode NFC and collapse irregular whitespaces.
        Preserves Chakma script characters, diacritics, and matras accurately.
        """
        if not text:
            return ""
        # 1. Unicode NFC normalization
        normalized = unicodedata.normalize("NFC", text)
        # 2. Strip leading/trailing whitespaces
        normalized = normalized.strip()
        # 3. Collapse multiple spaces into single space while preserving tokens
        normalized = " ".join(normalized.split())
        return normalized

    def load(self) -> None:
        """
        Load sentences and vocabulary from disk, ignore comment/blank lines,
        and normalize all text strings.
        """
        self._sentences.clear()
        self._vocabulary.clear()
        self._all_corpus_chars.clear()

        # 1. Load sentences
        if self.sentences_path.exists():
            with open(self.sentences_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    normalized = self.normalize_text(stripped)
                    if normalized:
                        self._sentences.append(normalized)
            logger.info(f"Loaded {len(self._sentences)} sentences from {self.sentences_path}")
        else:
            logger.warning(f"Sentences file not found at: {self.sentences_path}")

        # 2. Load vocabulary
        if self.vocabulary_path.exists():
            with open(self.vocabulary_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    normalized = self.normalize_text(stripped)
                    if normalized:
                        self._vocabulary.append(normalized)
            logger.info(f"Loaded {len(self._vocabulary)} vocabulary words from {self.vocabulary_path}")
        else:
            logger.warning(f"Vocabulary file not found at: {self.vocabulary_path}")

        # 3. Populate all unique characters in the corpus (excluding whitespace)
        all_text = "".join(self._sentences) + "".join(self._vocabulary)
        for char in all_text:
            if not char.isspace():
                self._all_corpus_chars.add(char)

    @property
    def sentences(self) -> List[str]:
        """Return list of loaded sentences."""
        return list(self._sentences)

    @property
    def vocabulary(self) -> List[str]:
        """Return list of loaded vocabulary words."""
        return list(self._vocabulary)

    def get_characters(self, text: Optional[str] = None) -> Set[str]:
        """
        Return unique non-whitespace characters in given text or the entire loaded corpus.
        """
        if text is not None:
            return {c for c in text if not c.isspace()}
        return set(self._all_corpus_chars)

    def get_supported_characters(self) -> Set[str]:
        """
        Return set of characters in corpus that are valid in the CharsetEngine.
        """
        return {c for c in self._all_corpus_chars if self.charset_engine.is_valid_char(c)}

    def get_unsupported_characters(self) -> Set[str]:
        """
        Return set of characters in corpus that are NOT registered in CharsetEngine.
        """
        return {c for c in self._all_corpus_chars if not self.charset_engine.is_valid_char(c)}

    def get_random_sentence(self, seed: Optional[int] = None) -> str:
        """
        Deterministically sample a random sentence from the corpus.
        """
        if not self._sentences:
            raise ValueError("Corpus contains no sentences. Load sentences before sampling.")

        rng = random.Random(seed) if seed is not None else self._rng
        return rng.choice(self._sentences)

    def get_random_sentences(self, count: int, seed: Optional[int] = None) -> List[str]:
        """
        Deterministically sample N random sentences from the corpus (with replacement).
        """
        if not self._sentences:
            raise ValueError("Corpus contains no sentences.")

        rng = random.Random(seed) if seed is not None else self._rng
        return [rng.choice(self._sentences) for _ in range(count)]

    def get_random_word(self, seed: Optional[int] = None) -> str:
        """
        Deterministically sample a random word from the vocabulary pool.
        """
        if not self._vocabulary:
            raise ValueError("Corpus contains no vocabulary words. Load vocabulary before sampling.")

        rng = random.Random(seed) if seed is not None else self._rng
        return rng.choice(self._vocabulary)

    def get_random_words(self, count: int, seed: Optional[int] = None) -> List[str]:
        """
        Deterministically sample N random words from the vocabulary pool.
        """
        if not self._vocabulary:
            raise ValueError("Corpus contains no vocabulary words.")

        rng = random.Random(seed) if seed is not None else self._rng
        return [rng.choice(self._vocabulary) for _ in range(count)]

    def validate(self) -> CorpusValidationReport:
        """
        Validate entire corpus against the canonical CharsetEngine:
        - Check for empty corpora
        - Detect unsupported Unicode characters or noise
        - Calculate frequency distribution of characters
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not self._sentences:
            warnings.append("No sentences loaded in corpus.")
        if not self._vocabulary:
            warnings.append("No vocabulary words loaded in corpus.")

        # Character validation
        unsupported = sorted(list(self.get_unsupported_characters()))
        supported = sorted(list(self.get_supported_characters()))

        if unsupported:
            errors.append(f"Found {len(unsupported)} unsupported characters in corpus: {unsupported}")

        # Character frequencies
        all_text = "".join(self._sentences) + "".join(self._vocabulary)
        char_counts = Counter(c for c in all_text if not c.isspace())

        is_valid = len(errors) == 0

        report = CorpusValidationReport(
            is_valid=is_valid,
            total_sentences=len(self._sentences),
            total_words=len(self._vocabulary),
            unique_characters_count=len(self._all_corpus_chars),
            supported_characters_count=len(supported),
            unsupported_characters_count=len(unsupported),
            unsupported_characters=unsupported,
            character_frequencies=dict(char_counts.most_common()),
            errors=errors,
            warnings=warnings,
        )

        if not is_valid:
            logger.error(f"Corpus validation FAILED: {errors}")
        else:
            logger.info(
                f"Corpus validation PASSED: {len(self._sentences)} sentences, "
                f"{len(self._vocabulary)} words, {len(supported)} unique valid characters."
            )

        return report
