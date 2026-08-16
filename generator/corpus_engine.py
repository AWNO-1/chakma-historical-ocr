"""
Corpus Engine for generating and sampling Chakma text lines and sequences.
"""

from pathlib import Path
from typing import List, Optional, Union
from utils.file_utils import read_text_lines, resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("corpus_engine")


class CorpusEngine:
    """
    Loads sentences and vocabulary to generate realistic Chakma text sequences.
    """

    def __init__(
        self,
        sentences_path: Union[str, Path] = "corpus/sentences.txt",
        vocabulary_path: Union[str, Path] = "corpus/vocabulary.txt",
    ):
        self.sentences_path = resolve_path(sentences_path)
        self.vocabulary_path = resolve_path(vocabulary_path)
        self.sentences: List[str] = []
        self.vocabulary: List[str] = []
        self._load_corpus()

    def _load_corpus(self) -> None:
        """Load sentences and vocabulary files."""
        if self.sentences_path.exists():
            self.sentences = read_text_lines(self.sentences_path)
            logger.info(f"Loaded {len(self.sentences)} sentences.")
        if self.vocabulary_path.exists():
            self.vocabulary = read_text_lines(self.vocabulary_path)
            logger.info(f"Loaded {len(self.vocabulary)} vocabulary words.")

    def sample_line(self, min_chars: int = 10, max_chars: int = 40) -> str:
        """
        Sample or construct a line of Chakma text.
        Skeleton implementation for Stage 01.
        """
        if self.sentences:
            return self.sentences[0]
        return ""

    def sample_paragraph(self, num_lines: int = 5) -> List[str]:
        """
        Sample multiple lines for a manuscript page.
        """
        return [self.sample_line() for _ in range(num_lines)]
