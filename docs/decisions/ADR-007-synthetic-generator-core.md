# ADR-007: In-Memory Synthetic Sample Generator Core Pipeline

## Status
Accepted

## Context
Following the implementation of individual engines (Corpus, Charset, Font, Layout, Renderer), the project requires a unified orchestrator (`SyntheticGenerator`) to connect these decoupled components into a cohesive pipeline that produces synthetic training samples for YOLO.

## Decision
1. **Pipeline Architecture**:
   - `SyntheticGenerator` serves as the central orchestrator connecting:
     - `CorpusEngine` for linguistic text source.
     - `CharsetEngine` for canonical validation against 71 classes.
     - `FontEngine` for typography and glyph support.
     - `LayoutEngine` for spatial geometry and reading order.
     - `LineRenderer` for continuous rasterization and character/cluster bounding box extraction.
2. **In-Memory Encapsulation**:
   - `SyntheticSample` holds raw PIL Image, list of `SampleCharacter` annotations, and `SampleMetadata` in memory.
   - Generation is purely in-memory; background compositing and augmentations are delegated to Stages 08 and 09.
3. **Deterministic Seeding**:
   - Every generation step accepts a seed and derives deterministic pseudo-random sequences for text selection, font choice, font size, margins, and rendering coordinates.

## Consequences
- Clean separation of concerns: Generator core focuses exclusively on text-to-image synthesis and ground truth annotation.
- Zero disk overhead during generation batches.
- Direct export compatibility with standard YOLO format (`class_id center_x center_y width height`).
