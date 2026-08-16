# Stage 02: Chakma Charset and Class Registry

## Stage Information
- **Title:** Chakma Charset and Class Registry
- **Stage Number:** 02
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Establish the authoritative single source of truth for Chakma script character classes, Unicode code point mappings, and contiguous class IDs for YOLO character detection and deterministic text reconstruction.

## Implementation Details
1. **Canonical Registry (`corpus/charset.json`):**
   - 71 distinct Chakma script characters verified directly against the official Unicode standard (Unicode Block `U+11100..U+1114F`).
   - Every class record contains: `id`, `unicode`, `character`, `name`, `category`, `unicode_general_category`.
   - Contiguous 0-indexed integer IDs: `0` to `70`.

2. **Category Hierarchy (`config/classes.yaml`):**
   - **`signs_and_modifiers` (5 classes, IDs 0-2, 51-52):** Candrabindu, Anusvara, Visarga, Virama, Maayyaa.
   - **`independent_vowels` (4 classes, IDs 3-6):** AA, I, U, E.
   - **`consonants` (34 classes, IDs 7-38, 67, 70):** KAA through HAA, LHAA, VAA.
   - **`dependent_vowels` (14 classes, IDs 39-50, 68-69):** Vowel signs A through AU, O Mark, AU Mark, Vowel signs AA, EI.
   - **`digits` (10 classes, IDs 53-62):** Digits 0 through 9.
   - **`punctuation` (4 classes, IDs 63-66):** Section Mark, Danda, Double Danda, Question Mark.

3. **Charset Engine (`generator/charset_engine.py`):**
   - `load_charset()`: High-performance O(1) indexed lookup tables in memory.
   - `get_class_by_id(id)`: Lookup class by integer ID.
   - `get_class_by_unicode(unicode_str)`: Lookup class by Unicode string.
   - `get_class_by_char(char)`: Lookup class by UTF-8 character.
   - `get_class_id(char_or_unicode)`: Resolve class ID.
   - `get_character(id)`: Resolve UTF-8 character string from class ID.
   - `get_all_classes()`: Retrieve complete immutable list of classes.
   - `get_classes_by_category(category)`: Filter classes by linguistic category.
   - `validate_charset()`: Integrity validation checking duplicate IDs, duplicate Unicode, missing/non-contiguous IDs, and config mismatches.

4. **Automated Unit Tests (`tests/test_charset.py`):**
   - 9 comprehensive test functions verifying integrity, lookups, mappings, category distribution, and error detection on corrupted datasets.

## Complete Class Inventory (71 Classes)

| ID | Unicode | Character | Unicode Name | Category |
|:---|:---|:---:|:---|:---|
| 0 | U+11100 | 𑄀 | CHAKMA SIGN CANDRABINDU | signs_and_modifiers |
| 1 | U+11101 | 𑄁 | CHAKMA SIGN ANUSVARA | signs_and_modifiers |
| 2 | U+11102 | 𑄂 | CHAKMA SIGN VISARGA | signs_and_modifiers |
| 3 | U+11103 | 𑄃 | CHAKMA LETTER AA | independent_vowels |
| 4 | U+11104 | 𑄄 | CHAKMA LETTER I | independent_vowels |
| 5 | U+11105 | 𑄅 | CHAKMA LETTER U | independent_vowels |
| 6 | U+11106 | 𑄆 | CHAKMA LETTER E | independent_vowels |
| 7 | U+11107 | 𑄇 | CHAKMA LETTER KAA | consonants |
| 8 | U+11108 | 𑄈 | CHAKMA LETTER KHAA | consonants |
| 9 | U+11109 | 𑄉 | CHAKMA LETTER GAA | consonants |
| 10 | U+1110A | 𑄊 | CHAKMA LETTER GHAA | consonants |
| 11 | U+1110B | 𑄋 | CHAKMA LETTER NGAA | consonants |
| 12 | U+1110C | 𑄌 | CHAKMA LETTER CAA | consonants |
| 13 | U+1110D | 𑄍 | CHAKMA LETTER CHAA | consonants |
| 14 | U+1110E | 𑄎 | CHAKMA LETTER JAA | consonants |
| 15 | U+1110F | 𑄏 | CHAKMA LETTER JHAA | consonants |
| 16 | U+11110 | 𑄐 | CHAKMA LETTER NYAA | consonants |
| 17 | U+11111 | 𑄑 | CHAKMA LETTER TTAA | consonants |
| 18 | U+11112 | 𑄒 | CHAKMA LETTER TTHAA | consonants |
| 19 | U+11113 | 𑄓 | CHAKMA LETTER DDAA | consonants |
| 20 | U+11114 | 𑄔 | CHAKMA LETTER DDHAA | consonants |
| 21 | U+11115 | 𑄕 | CHAKMA LETTER NNAA | consonants |
| 22 | U+11116 | 𑄖 | CHAKMA LETTER TAA | consonants |
| 23 | U+11117 | 𑄗 | CHAKMA LETTER THAA | consonants |
| 24 | U+11118 | 𑄘 | CHAKMA LETTER DAA | consonants |
| 25 | U+11119 | 𑄙 | CHAKMA LETTER DHAA | consonants |
| 26 | U+1111A | 𑄚 | CHAKMA LETTER NAA | consonants |
| 27 | U+1111B | 𑄛 | CHAKMA LETTER PAA | consonants |
| 28 | U+1111C | 𑄜 | CHAKMA LETTER PHAA | consonants |
| 29 | U+1111D | 𑄝 | CHAKMA LETTER BAA | consonants |
| 30 | U+1111E | 𑄞 | CHAKMA LETTER BHAA | consonants |
| 31 | U+1111F | 𑄟 | CHAKMA LETTER MAA | consonants |
| 32 | U+11120 | 𑄠 | CHAKMA LETTER YYAA | consonants |
| 33 | U+11121 | 𑄡 | CHAKMA LETTER YAA | consonants |
| 34 | U+11122 | 𑄢 | CHAKMA LETTER RAA | consonants |
| 35 | U+11123 | 𑄣 | CHAKMA LETTER LAA | consonants |
| 36 | U+11124 | 𑄤 | CHAKMA LETTER WAA | consonants |
| 37 | U+11125 | 𑄥 | CHAKMA LETTER SAA | consonants |
| 38 | U+11126 | 𑄦 | CHAKMA LETTER HAA | consonants |
| 39 | U+11127 | 𑄧 | CHAKMA VOWEL SIGN A | dependent_vowels |
| 40 | U+11128 | 𑄨 | CHAKMA VOWEL SIGN I | dependent_vowels |
| 41 | U+11129 | 𑄩 | CHAKMA VOWEL SIGN II | dependent_vowels |
| 42 | U+1112A | 𑄪 | CHAKMA VOWEL SIGN U | dependent_vowels |
| 43 | U+1112B | 𑄫 | CHAKMA VOWEL SIGN UU | dependent_vowels |
| 44 | U+1112C | 𑄬 | CHAKMA VOWEL SIGN E | dependent_vowels |
| 45 | U+1112D | 𑄭 | CHAKMA VOWEL SIGN AI | dependent_vowels |
| 46 | U+1112E | 𑄮 | CHAKMA VOWEL SIGN O | dependent_vowels |
| 47 | U+1112F | 𑄯 | CHAKMA VOWEL SIGN AU | dependent_vowels |
| 48 | U+11130 | 𑄰 | CHAKMA VOWEL SIGN OI | dependent_vowels |
| 49 | U+11131 | 𑄱 | CHAKMA O MARK | dependent_vowels |
| 50 | U+11132 | 𑄲 | CHAKMA AU MARK | dependent_vowels |
| 51 | U+11133 | 𑄳 | CHAKMA VIRAMA | signs_and_modifiers |
| 52 | U+11134 | 𑄴 | CHAKMA MAAYYAA | signs_and_modifiers |
| 53 | U+11136 | 𑄶 | CHAKMA DIGIT ZERO | digits |
| 54 | U+11137 | 𑄷 | CHAKMA DIGIT ONE | digits |
| 55 | U+11138 | 𑄸 | CHAKMA DIGIT TWO | digits |
| 56 | U+11139 | 𑄹 | CHAKMA DIGIT THREE | digits |
| 57 | U+1113A | 𑄺 | CHAKMA DIGIT FOUR | digits |
| 58 | U+1113B | 𑄻 | CHAKMA DIGIT FIVE | digits |
| 59 | U+1113C | 𑄼 | CHAKMA DIGIT SIX | digits |
| 60 | U+1113D | 𑄽 | CHAKMA DIGIT SEVEN | digits |
| 61 | U+1113E | 𑄾 | CHAKMA DIGIT EIGHT | digits |
| 62 | U+1113F | 𑄿 | CHAKMA DIGIT NINE | digits |
| 63 | U+11140 | 𑅀 | CHAKMA SECTION MARK | punctuation |
| 64 | U+11141 | 𑅁 | CHAKMA DANDA | punctuation |
| 65 | U+11142 | 𑅂 | CHAKMA DOUBLE DANDA | punctuation |
| 66 | U+11143 | 𑅃 | CHAKMA QUESTION MARK | punctuation |
| 67 | U+11144 | 𑅄 | CHAKMA LETTER LHAA | consonants |
| 68 | U+11145 | 𑅅 | CHAKMA VOWEL SIGN AA | dependent_vowels |
| 69 | U+11146 | 𑅆 | CHAKMA VOWEL SIGN EI | dependent_vowels |
| 70 | U+11147 | 𑅇 | CHAKMA LETTER VAA | consonants |

## Verification & Test Results
- Pytest test suite: 24 tests passed in 5.94s (100% pass rate).
- Registry Validation: `validate_charset()` returned `is_valid: True`, 0 duplicate IDs, 0 duplicate Unicode points, 0 missing contiguous IDs, 0 config mismatches.
- Unresolved Items: 0 (all 71 defined code points are definitively assigned and verified).
