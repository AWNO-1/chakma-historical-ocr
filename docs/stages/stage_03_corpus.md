# Stage 03: Chakma Corpus Engine

## Stage Information
- **Title:** Chakma Corpus Engine
- **Stage Number:** 03
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Implement an authoritative, deterministic, and Unicode-normalized linguistic Corpus Engine (`generator/corpus_engine.py`) responsible for loading, validating, and sampling authentic Chakma sentences and vocabulary pools for the synthetic manuscript generator without using OCR models.

## Implementation Details
1. **Corpus Files (`corpus/sentences.txt`, `corpus/vocabulary.txt`):**
   - Authentic Chakma script sentences and vocabulary words.
   - Support for comment headers (`#`) and automated blank-line filtering.
2. **Authoritative Engine (`generator/corpus_engine.py`):**
   - `load()`: Loads raw texts, removes comments/empty lines, applies Unicode NFC normalization and whitespace sanitation.
   - `validate()`: Comprehensive linguistic validation cross-referencing all corpus glyphs against the canonical 71 Chakma classes in `CharsetEngine`.
   - `get_random_sentence(seed=None)` & `get_random_sentences(count, seed=None)`: Deterministic sentence selection.
   - `get_random_word(seed=None)` & `get_random_words(count, seed=None)`: Deterministic vocabulary word selection.
   - `get_characters()`: Retrieves all unique non-whitespace characters present in corpus or input text.
   - `get_supported_characters()`: Identifies all valid Chakma characters.
   - `get_unsupported_characters()`: Flags and isolates any foreign/unsupported symbols.
   - `normalize_text(text)`: Static Unicode NFC normalizer.
3. **Unit Tests (`tests/test_corpus.py`):**
   - 8 comprehensive test functions covering file loading, empty lines/comments filtering, Unicode NFC normalization, deterministic seed reproducibility, seed override, supported/unsupported character detection, and empty corpus error handling.
4. **Demonstration Utility (`utils/demo_corpus.py`):**
   - Console inspection utility displaying loading metrics, character frequencies, and real output examples.

## Real Output Demonstration (Seed=42)

### 1. Corpus Loading & Verification
- **Sentences Loaded:** 10 sentences
- **Vocabulary Loaded:** 30 words
- **Unique Characters in Corpus:** 37
- **Supported Valid Characters:** 37 (100% compliant with Unicode block U+11100..U+1114F)
- **Unsupported Characters Detected:** 0
- **Validation Status:** `is_valid: True`

### 2. Sample Deterministic Sentences
1. `𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁`
2. `𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁`
3. `𑄌𑄋𑄴𑄟 𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨 𑄃𑄢𑄴 𑄞𑄌𑄴 𑄃𑄟𑄢𑄴 𑄉𑄧𑄢𑄧𑄛𑄴𑅂`

### 3. Sample Deterministic Vocabulary Words
1. `𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨`
2. `𑄘𑄬𑄌𑄴`
3. `𑄌𑄋𑄴𑄟`
4. `𑄥𑄨𑄊𑄮𑄚𑄴`
5. `𑄇𑄨𑄖𑄛𑄴`
6. `𑄛𑄧𑄖𑄴`

### 4. Character Frequencies Top 10
- `𑄴` (ID: 52, CHAKMA MAAYYAA): 55 occurrences
- `𑄢` (ID: 34, CHAKMA LETTER RAA): 25 occurrences
- `𑄧` (ID: 39, CHAKMA VOWEL SIGN A): 25 occurrences
- `𑄨` (ID: 40, CHAKMA VOWEL SIGN I): 24 occurrences
- `𑄌` (ID: 12, CHAKMA LETTER CAA): 21 occurrences
- `𑄬` (ID: 44, CHAKMA VOWEL SIGN E): 18 occurrences
- `𑄟` (ID: 31, CHAKMA LETTER MAA): 17 occurrences
- `𑄚` (ID: 26, CHAKMA LETTER NAA): 16 occurrences
- `𑄖` (ID: 22, CHAKMA LETTER TAA): 14 occurrences
- `𑄇` (ID:  7, CHAKMA LETTER KAA): 13 occurrences

## Verification Results
- **Pytest Pass Rate:** 100% (30/30 passed in 5.63s).
- **Reproducibility Test:** Identical outputs generated across independent seeds and multiple test invocations.
