# ADR-001: Project Architecture and Single-Model OCR Strategy

## Status
Accepted

## Date
2026-08-17

## Context
Historical Chakma manuscripts present unique challenges:
- Rare endangered Brahmic-family script with distinctive ligatures and diacritics.
- Aged, degraded background media (palm leaf, handmade paper, parchment, bamboo).
- Scarcity of labeled ground-truth real manuscript data.
- Complex character touching, ink bleed, and fading.

Standard traditional OCR pipelines often employ heavy multi-stage neural architectures:
- Separate line detection models (e.g. CRAFT, DBNet)
- Word segmentation models
- Sequence recognition models (CRNN, CTC, TrOCR, Transformer OCR)
- Language model decoders

These multi-stage neural pipelines introduce compounding error propagation, high latency, huge training data requirements, and fragile failure modes on historical low-resource scripts.

## Decision
We establish the following foundational architectural principles:
1. **Single Neural Model Rule:** YOLO (Ultralytics YOLO) is the **exclusive** neural model across the entire project. It is strictly tasked with character detection and character classification.
2. **No Secondary Neural Models:** Explicitly forbidden to use Tesseract, TrOCR, CRNN, CTC, Transformer OCR, separate neural line segmenters, or word segmenters.
3. **Deterministic Text Reconstruction:** Reconstruction of words, lines, paragraphs, and reading order is accomplished through purely deterministic geometric post-processing algorithms (bounding box clustering, spatial coordinate sorting, inter-character gap thresholding).
4. **Reproducibility First:** Central seed enforcement across Python, NumPy, and PyTorch. All configurations parameterized in YAML files with dynamic relative path resolution.

## Consequences
### Positive
- Simplicity and high inference speed.
- Modular, testable, and deterministic post-processing.
- Direct character bounding box interpretability and easy visual debugging.
- Low compute requirement for training and inference.

### Negative / Mitigations
- Requires high-precision character detection from YOLO, especially on overlapping diacritics.
- Handled via advanced synthetic data generation with pixel-perfect ground truth bounding boxes.
