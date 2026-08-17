# ADR-003: Corpus Engine Architecture and Deterministic Linguistic Sampling

## Status
Accepted

## Date
2026-08-17

## Context
The synthetic manuscript generation pipeline requires high-quality, authentic Chakma script text streams (sentences, phrases, and vocabulary words).
Text inputs must be strictly validated against the canonical 71-class character registry (`corpus/charset.json`), normalized for consistent glyph rendering, and sampled deterministically to guarantee complete dataset reproducibility across different machines and runs.

## Decision
1. **Corpus Source Architecture:** Maintain independent, easily extensible text assets in plain UTF-8 format (`corpus/sentences.txt` and `corpus/vocabulary.txt`), with support for inline/block comment headers (`#`) and automated blank line suppression.
2. **Text Normalization Strategy:** Enforce standard Unicode NFC normalization (`unicodedata.normalize('NFC', text)`) combined with whitespace collapsing (`" ".join(text.split())`) on all loaded tokens to prevent decomposed diacritics and irregular spacing from breaking bounding box annotations.
3. **Deterministic Sampling:** Encapsulate random selection inside isolated `random.Random(seed)` instances. All sampling methods (`get_random_sentence`, `get_random_sentences`, `get_random_word`, `get_random_words`) accept an optional local seed override while defaulting to the engine's central seed.
4. **Charset Integration & Unsupported Character Rejection:** Every token in the corpus is cross-referenced against `CharsetEngine.is_valid_char()`. If any unsupported glyph (such as Latin noise, unassigned codepoints, or invalid punctuation) is detected, `CorpusEngine.validate()` flags `is_valid = False` with detailed reporting.
5. **No Auxiliary OCR:** Text generation, corpus sampling, and linguistic validation are 100% deterministic and do not rely on any neural networks or OCR engines.

## Consequences
### Positive
- Fully reproducible synthetic datasets generated from fixed random seeds.
- Guaranteed zero out-of-vocabulary or unmapped glyphs reaching the rendering and annotation pipeline.
- Clean separation between linguistic text data and subsequent font rendering engines.

### Constraints
- New corpus additions must contain exclusively valid Chakma Unicode characters (U+11100..U+1114F).
