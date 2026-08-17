# ADR-004: Chakma Script Font Selection & Verification Policy

## Context
Synthetic pre-training for Chakma Historical OCR requires fonts that accurately render the Chakma Unicode block (`U+11100..U+1114F`). Fonts must not be accepted based merely on file names; they must undergo deep OpenType table parsing and visual rendering verification.

## Decisions
1. **Quality Threshold**:
   - `FULL_SUPPORT` ($\ge 70\%$ Chakma glyph coverage) $\rightarrow$ Candidate for synthetic pre-training.
   - `PARTIAL_SUPPORT` ($> 0\%$ and $< 70\%$) $\rightarrow$ Excluded from default synthetic training.
   - `NO_CHAKMA_SUPPORT` ($0\%$) $\rightarrow$ Rejected immediately and placed in `fonts/rejected/`.
2. **Deduplication**:
   - Fonts with identical SHA-256 binary hash are deduplicated.
3. **Registry Management**:
   - `config/fonts.yaml` is the single source of truth for runtime font enablement.
4. **Isolated vs Shaped Text**:
   - Both isolated rendering and complex OpenType text shaping (`GSUB`/`GPOS`) are classified and tracked in `fonts/metadata/<font_id>.json`.

## Consequences
- 12 distinct, high-coverage Chakma fonts are registered for diverse synthetic generation.
- Zero risk of blank or tofu glyphs corrupting synthetic training data.
