# Changelog

All notable changes to the Chakma Historical OCR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.3.0] - 2026-08-17 - Stage 03: Chakma Corpus Engine

### Added
- Authoritative `CorpusEngine` in `generator/corpus_engine.py` with support for Unicode NFC normalization, comment and empty line suppression, and deterministic random sampling.
- Authentic sample Chakma corpus files in `corpus/sentences.txt` and `corpus/vocabulary.txt`.
- Multi-tier validation in `CorpusEngine.validate()` checking total sentences, vocabulary count, character frequency distribution, and detecting unsupported foreign characters.
- Expanded test suite `tests/test_corpus.py` with 8 dedicated unit tests covering loading, empty line handling, NFC normalization, seed reproducibility, character extraction, and corrupt dataset error handling (30 tests total in project suite).
- Demonstration utility `utils/demo_corpus.py` for verifying real output samples and character distribution.
- Architectural Decision Record `ADR-003-corpus-engine.md`.
- Documentation report `docs/stages/stage_03_corpus.md`.

## [0.2.0] - 2026-08-17 - Stage 02: Chakma Charset and Class Registry

### Added
- Authoritative canonical character registry in `corpus/charset.json` containing 71 verified Chakma script classes based on Unicode block `U+11100..U+1114F`.
- Strict contiguous 0-indexed class ID allocation (`0` to `70`) in ascending code point order.
- Comprehensive `CharsetEngine` in `generator/charset_engine.py` with O(1) in-memory lookup tables (`get_class_by_id`, `get_class_by_unicode`, `get_class_by_char`, `get_class_id`, `get_character`, `get_all_classes`, `validate_charset`).
- Multi-dimensional validation in `validate_charset()` enforcing ID uniqueness, Unicode uniqueness, character uniqueness, index contiguity, and cross-file config consistency.
- Updated `config/classes.yaml` specifying class groups and count distributions.
- Expanded test suite `tests/test_charset.py` with 9 dedicated unit tests covering lookups, mappings, category counts, and corruption detection (24 tests total in project suite).
- Architectural Decision Record `ADR-002-chakma-charset.md`.
- Documentation report `docs/stages/stage_02_charset.md`.

## [0.1.0] - 2026-08-17 - Stage 01: Project Initialization and Repository Structure

### Added
- Standardized directory layout (`corpus/`, `config/`, `fonts/`, `data/`, `generator/`, `training/`, `inference/`, `debug/`, `utils/`, `tests/`, `docs/`, `experiments/`).
- Central YAML configuration files (`project.yaml`, `classes.yaml`, `synthetic.yaml`, `training.yaml`).
- Core utilities in `utils/` (`seed.py`, `logging_utils.py`, `file_utils.py`, `geometry.py`, `image_utils.py`).
- Modular skeleton modules in `generator/` for synthetic manuscript generation.
- Training and evaluation pipeline skeletons in `training/`.
- Inference wrapper and deterministic text reconstruction engine in `inference/`.
- Debug visualization scripts in `debug/`.
- Diagnostic entry point `main.py` verifying system environment, dependencies, seed, and repo integrity.
- Architecture Decision Record `ADR-001-project-architecture.md`.
- Documentation for Stage 01 in `docs/stages/stage-01.md`.
