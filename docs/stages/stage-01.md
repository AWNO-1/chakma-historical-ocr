# Stage 01: Project Initialization and Repository Structure

## Stage Information
- **Title:** Project Initialization and Repository Structure
- **Stage Number:** 01
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Establish the standardized, modular, and reproducible repository foundation for the Chakma Historical OCR system, adhering strictly to the single-model YOLO architecture and deterministic text reconstruction.

## Implementation Details
1. **Directory Hierarchy:**
   - `corpus/`: Charset schemas, vocabulary lists, and seed sentences.
   - `config/`: Central project, character classes, synthetic generation, and training configurations.
   - `fonts/`: Typography storage for Chakma TrueType/OpenType fonts.
   - `data/`: Categorized backgrounds (paper, parchment, manuscript, bamboo, miscellaneous), synthetic datasets, and real manuscript annotations.
   - `generator/`: Modular skeleton engines for synthetic manuscript rendering (charset, corpus, font, layout, line renderer, background, augmentations, transform, annotation).
   - `training/`: Dataset adapter, validation, and evaluation pipeline skeletons.
   - `inference/`: YOLO character detector wrapper and purely deterministic text reconstruction engine.
   - `debug/`: Visual inspection tools for synthetic data, ground truth YOLO labels, and detector predictions.
   - `utils/`: Centralized seed configuration, structured logging, dynamic path resolution, geometry primitives (BBox, IoU, reading order sorting), and image processing.
   - `tests/`: Automated unit and integration test suite.
   - `docs/`: Architectural Decision Records (ADRs), stage reports, and experiment documentation.
   - `experiments/`: Experiment runs, benchmarks, and artifacts.

2. **System Diagnostic Entry Point (`main.py`):**
   - Environment and runtime inspection (OS, Python 3.13, PyTorch, CUDA status).
   - Key dependency check.
   - Central seed configuration and verification.
   - Automated project repository structure integrity verification.

## Verification & Tests
- Automated Pytest suite covering geometry (BBox, IoU, reading order), charset, corpus, font engines, synthetic annotations, and pipeline integrity.
- `main.py` executed successfully with all components reporting green.
