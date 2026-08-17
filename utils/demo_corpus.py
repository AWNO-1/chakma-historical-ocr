"""
Demonstration script for Chakma Corpus Engine.
Displays loading stats, character inventory validation, and deterministic random sampling.
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.corpus_engine import CorpusEngine


def demo():
    print("=" * 65)
    print("        CHAKMA CORPUS ENGINE - DEMONSTRATION & VALIDATION       ")
    print("=" * 65)

    engine = CorpusEngine(seed=42)
    report = engine.validate()

    print(f"\n[1] CORPUS LOAD STATUS:")
    print(f"  * Sentences loaded : {len(engine.sentences)}")
    print(f"  * Vocabulary loaded: {len(engine.vocabulary)}")
    print(f"  * Unique characters: {report.unique_characters_count}")
    print(f"  * Supported chars  : {report.supported_characters_count}")
    print(f"  * Unsupported chars: {report.unsupported_characters_count}")
    print(f"  * Validation Valid : {report.is_valid}")

    print("\n[2] SAMPLE DETERMINISTIC SENTENCES (Seed=42):")
    samples = engine.get_random_sentences(3, seed=42)
    for i, s in enumerate(samples, 1):
        print(f"  {i}. {s}")

    print("\n[3] SAMPLE DETERMINISTIC VOCABULARY WORDS (Seed=42):")
    words = engine.get_random_words(6, seed=42)
    for i, w in enumerate(words, 1):
        print(f"  {i}. {w}")

    print("\n[4] CHARACTER FREQUENCY TOP 10:")
    freq_items = list(report.character_frequencies.items())[:10]
    for char, freq in freq_items:
        cls_id = engine.charset_engine.get_class_id(char)
        cls_name = engine.charset_engine.get_class_by_id(cls_id).name if cls_id is not None else "UNKNOWN"
        print(f"  * Char '{char}' (ID: {cls_id:2d}, {cls_name}): {freq:2d} occurrences")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    demo()
