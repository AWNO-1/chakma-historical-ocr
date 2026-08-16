# ADR-002: Canonical Chakma Script Character Registry and Class ID Allocation

## Status
Accepted

## Date
2026-08-17

## Context
A character-level OCR system requires a permanent, authoritative, and unambiguous character inventory.
For historical Chakma script (ISO 15924: Cakm), character classification and bounding-box detection rely on integer class IDs. Any change, re-indexing, collision, or ambiguous character definition in later stages would invalidate all synthetic datasets, ground-truth annotations, and trained YOLO model weights.

## Decision
1. **Single Source of Truth:** `corpus/charset.json` is the sole canonical authority for character definitions. No other independent class list is permitted.
2. **Standard Alignment:** All character code points are directly verified against the official Unicode Standard (Chakma Block: `U+11100 .. U+1114F`, including extensions up to Unicode 13.0). Zero invented Unicode values.
3. **Class Count & Inventory (71 Classes):**
   - **Signs and Modifiers (5):** Candrabindu (`U+11100`), Anusvara (`U+11101`), Visarga (`U+11102`), Virama (`U+11133`), Maayyaa (`U+11134`).
   - **Independent Vowels (4):** AA (`U+11103`), I (`U+11104`), U (`U+11105`), E (`U+11106`).
   - **Consonants (34):** KAA through HAA (`U+11107..U+11126`), LHAA (`U+11144`), VAA (`U+11147`).
   - **Dependent Vowels / Matras (14):** A, I, II, U, UU, E, AI, O, AU, OI, O MARK, AU MARK (`U+11127..U+11132`), AA (`U+11145`), EI (`U+11146`).
   - **Digits (10):** Chakma Digits 0-9 (`U+11136..U+1113F`).
   - **Punctuation (4):** Section Mark (`U+11140`), Danda (`U+11141`), Double Danda (`U+11142`), Question Mark (`U+11143`).
4. **Deterministic Class ID Invariant:** Class IDs are assigned contiguously from `0` to `70` in ascending Unicode code point order. IDs are strictly immutable across all project phases.
5. **Automated Verification:** `CharsetEngine.validate_charset()` enforces ID uniqueness, Unicode uniqueness, character uniqueness, index contiguity (`0..N-1`), and consistency with `config/classes.yaml`.

## Consequences
### Positive
- Strict reproducibility across synthetic generator, annotations, YOLO training labels, and inference.
- Complete coverage of classical and modern Chakma orthography.
- Elimination of class ID drift or off-by-one errors.

### Constraints
- Modifying the class registry requires a formal architectural review, ADR amendment, and dataset re-generation.
