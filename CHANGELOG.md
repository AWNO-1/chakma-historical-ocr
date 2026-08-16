# Changelog

All notable changes to the Chakma Historical OCR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-08-17 - Stage 01: Project Initialization and Repository Structure

### Added
- Standardized directory layout (`corpus/`, `config/`, `fonts/`, `data/`, `generator/`, `training/`, `inference/`, `debug/`, `utils/`, `tests/`, `docs/`, `experiments/`).
- Central YAML configuration files (`project.yaml`, `classes.yaml`, `synthetic.yaml`, `training.yaml`).
- Core utilities in `utils/`:
  - `seed.py`: Centralized reproducibility seed manager.
  - `logging_utils.py`: Structured console and file logger.
  - `file_utils.py`: Dynamic root path resolution, safe YAML/JSON/Text loaders.
  - `geometry.py`: BBox dataclass, YOLO coordinate conversion, IoU calculation, deterministic reading order sorting.
  - `image_utils.py`: Image loading, canvas creation, and visual overlay tools.
- Modular skeleton modules in `generator/` for synthetic manuscript generation.
- Training and evaluation pipeline skeletons in `training/`.\n- Inference wrapper and deterministic text reconstruction engine in `inference/`.
- Debug visualization scripts in `debug/`.
- Diagnostic entry point `main.py` verifying system environment, dependencies, seed, and repo integrity.
- Automated unit test suite in `tests/` (`test_charset.py`, `test_corpus.py`, `test_fonts.py`, `test_geometry.py`, `test_generator.py`, `test_pipeline.py`).
- Architecture Decision Record `ADR-001-project-architecture.md`.
- Documentation for Stage 01 in `docs/stages/stage-01.md`.
