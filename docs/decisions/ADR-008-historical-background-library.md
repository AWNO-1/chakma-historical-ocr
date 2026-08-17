# ADR-008: Real Historical Background Library and In-Memory Loader

## Status
Accepted

## Context
Synthetic historical manuscript generation requires realistic paper, parchment, and aged manuscript surfaces. Procedural solid colors lack authentic fiber texture, stains, and aging gradients, while generating backgrounds via generative ML introduces unnatural artifacts, slow inference, and dependency bloat.

## Decision
1. **Real Asset Library**:
   - Collect and categorize authentic digitized manuscript surfaces under `data/backgrounds/{category}/` (e.g. `paper`, `parchment`, `manuscript`, `bamboo`, `miscellaneous`).
2. **In-Memory Loading & Processing**:
   - Background images are loaded directly into RAM using PIL without writing intermediate tiles to disk.
   - Resizing and cropping uses aspect-ratio-preserving scaling and random window extraction, preventing stretching distortions and visible repeating seams.
3. **Robust Quarantine**:
   - Any corrupt or unreadable files are quarantined with explicit logging and excluded from active sampling pools.
4. **Deterministic Seeding**:
   - Category selection, image choice, and spatial crop coordinates are strictly governed by RNG seed.

## Consequences
- Authentic manuscript aesthetics without generative ML complexity or performance overhead.
- Fully decoupled module callable by `SyntheticGenerator` during compositing.
- Zero disk footprint during batch sample generation.
