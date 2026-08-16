# Chakma Historical OCR: YOLO-Based Character Detection & Text Reconstruction

An end-to-end Optical Character Recognition (OCR) system tailored for historical Chakma script manuscripts, combining deep learning object detection with deterministic spatial post-processing.

---

## 🏛️ Core Architectural Principles

1. **Single Neural Model:** YOLO is the **sole** neural model in the system, exclusively handling Character Detection and Character Classification.
2. **Zero Secondary Neural Networks:** Strictly no Tesseract, TrOCR, CRNN, CTC, Transformer OCR, separate neural line segmenters, or word detectors.
3. **Deterministic Text Reconstruction:** Words, lines, and reading order are reconstructed purely through geometric spatial clustering (Bounding Boxes, Class IDs, and spatial coordinates).
4. **Reproducibility First:** Central seed enforcement across Python, NumPy, and PyTorch.

---

## 📁 Repository Structure

```
chakma/
├── corpus/               # Chakma character sets, vocabulary, sentences
│   ├── sentences.txt
│   ├── vocabulary.txt
│   └── charset.json
├── config/               # Parameterized YAML configurations
│   ├── project.yaml
│   ├── classes.yaml
│   ├── synthetic.yaml
│   └── training.yaml
├── fonts/                # Chakma OpenType/TrueType fonts
├── data/
│   ├── backgrounds/      # Historical paper, parchment, manuscript, bamboo backgrounds
│   ├── synthetic/        # Generated synthetic datasets (images & YOLO labels)
│   └── real/             # Real historical manuscript scans & annotations
├── generator/            # Modular synthetic manuscript rendering engine
├── training/             # YOLO detector training & validation scripts
├── inference/            # YOLO detection wrapper & deterministic reconstructor
├── debug/                # Visualization tools for synthetic data, labels, and predictions
├── utils/                # Seed, logging, dynamic path, geometry, and image utilities
├── tests/                # Automated unit and integration test suite
├── docs/                 # Architectural Decision Records (ADRs) and stage reports
│   ├── stages/
│   ├── decisions/
│   └── experiments/
├── experiments/          # Experiment logs, metrics, and checkpoints
├── main.py               # System diagnostic and integrity check
├── requirements.txt      # Project dependencies
└── CHANGELOG.md          # Stage-by-stage release log
```

---

## 🚀 Quick Start & System Diagnostic

Run the system diagnostic to verify your environment and repository integrity:

```bash
python main.py
```

Run the automated test suite:

```bash
pytest -v
```

---

## ⚙️ Development Governance

The project follows a **Stage-by-Stage Approval** workflow. No stage is executed without explicit user approval (`APPROVED` / `CONTINUE`).
