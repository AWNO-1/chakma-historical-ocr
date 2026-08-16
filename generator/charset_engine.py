"""
Authoritative Charset Engine and Class Registry for Chakma Historical OCR.
Serves as the single source of truth for Chakma script character mapping, Unicode resolution, and class ID lookups.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from utils.file_utils import load_json, load_yaml, resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("charset_engine")


@dataclass(frozen=True)
class ChakmaClass:
    """
    Immutable representation of an individual Chakma character class.
    """
    id: int
    unicode: str
    character: str
    name: str
    category: str
    unicode_general_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CharsetValidationError(Exception):
    """Raised when charset validation fails."""
    pass


class CharsetEngine:
    """
    Single source of truth manager for the Chakma character set and YOLO class IDs.
    """

    def __init__(
        self,
        charset_path: Union[str, Path] = "corpus/charset.json",
        config_path: Optional[Union[str, Path]] = "config/classes.yaml",
    ):
        self.charset_path = resolve_path(charset_path)
        self.config_path = resolve_path(config_path) if config_path else None

        self._classes: List[ChakmaClass] = []
        self._id_to_class: Dict[int, ChakmaClass] = {}
        self._unicode_to_class: Dict[str, ChakmaClass] = {}
        self._char_to_class: Dict[str, ChakmaClass] = {}
        self._category_to_classes: Dict[str, List[ChakmaClass]] = {}

        self.load_charset()

    def load_charset(self) -> None:
        """
        Load charset from JSON file into indexed memory structures.
        """
        if not self.charset_path.exists():
            logger.error(f"Charset file not found at: {self.charset_path}")
            raise FileNotFoundError(f"Charset file does not exist: {self.charset_path}")

        data = load_json(self.charset_path)
        raw_classes = data.get("classes", [])

        self._classes.clear()
        self._id_to_class.clear()
        self._unicode_to_class.clear()
        self._char_to_class.clear()
        self._category_to_classes.clear()

        for item in raw_classes:
            cls_obj = ChakmaClass(
                id=int(item["id"]),
                unicode=str(item["unicode"]).strip().upper(),
                character=str(item["character"]),
                name=str(item["name"]),
                category=str(item["category"]),
                unicode_general_category=item.get("unicode_general_category"),
            )
            self._classes.append(cls_obj)
            self._id_to_class[cls_obj.id] = cls_obj
            self._unicode_to_class[cls_obj.unicode] = cls_obj
            self._char_to_class[cls_obj.character] = cls_obj

            self._category_to_classes.setdefault(cls_obj.category, []).append(cls_obj)

        logger.info(f"Successfully loaded {len(self._classes)} Chakma classes from {self.charset_path}")

    @property
    def total_classes(self) -> int:
        """Return total number of registered classes."""
        return len(self._classes)

    @property
    def num_classes(self) -> int:
        """Alias for total_classes for detector compatibility."""
        return len(self._classes)

    def get_class_by_id(self, class_id: int) -> Optional[ChakmaClass]:
        """Retrieve class definition by integer ID."""
        return self._id_to_class.get(class_id)

    def get_class_by_unicode(self, unicode_codepoint: str) -> Optional[ChakmaClass]:
        """Retrieve class definition by Unicode string (e.g. 'U+11100')."""
        formatted = unicode_codepoint.strip().upper()
        if not formatted.startswith("U+"):
            formatted = f"U+{formatted}"
        return self._unicode_to_class.get(formatted)

    def get_class_by_char(self, char: str) -> Optional[ChakmaClass]:
        """Retrieve class definition by UTF-8 character string."""
        return self._char_to_class.get(char)

    def get_class_id(self, char_or_unicode: str) -> Optional[int]:
        """
        Get integer class ID from either character or Unicode string.
        """
        if char_or_unicode in self._char_to_class:
            return self._char_to_class[char_or_unicode].id

        formatted = char_or_unicode.strip().upper()
        if not formatted.startswith("U+"):
            formatted = f"U+{formatted}"
        if formatted in self._unicode_to_class:
            return self._unicode_to_class[formatted].id

        return None

    def get_character(self, class_id: int) -> Optional[str]:
        """Retrieve UTF-8 character string for a given class ID."""
        cls_obj = self._id_to_class.get(class_id)
        return cls_obj.character if cls_obj else None

    def get_all_classes(self) -> List[ChakmaClass]:
        """Return all registered Chakma classes in ascending ID order."""
        return list(self._classes)

    def get_classes_by_category(self, category: str) -> List[ChakmaClass]:
        """Return all classes belonging to a specific linguistic category."""
        return list(self._category_to_classes.get(category, []))

    def get_id_to_char_map(self) -> Dict[int, str]:
        """Return mapping from integer class ID to character string."""
        return {c.id: c.character for c in self._classes}

    def get_id_to_name_map(self) -> Dict[int, str]:
        """Return mapping from integer class ID to character name."""
        return {c.id: c.name for c in self._classes}

    def is_valid_char(self, char: str) -> bool:
        """Check if character exists in registry."""
        return char in self._char_to_class

    def validate_charset(self) -> Dict[str, Any]:
        """
        Perform rigorous integrity checks on the charset registry:
        - Duplicate IDs
        - Duplicate Unicode code points
        - Duplicate characters
        - Missing IDs (contiguous sequence 0..N-1)
        - Malformed entries (missing required fields)
        - Cross-file consistency between charset.json and config/classes.yaml

        Returns:
            Dict containing validation summary, boolean 'is_valid', and error messages if any.
        """
        errors: List[str] = []
        warnings: List[str] = []

        seen_ids: Set[int] = set()
        duplicate_ids: List[int] = []

        seen_unicodes: Set[str] = set()
        duplicate_unicodes: List[str] = []

        seen_chars: Set[str] = set()
        duplicate_chars: List[str] = []

        # 1. Inspect loaded classes
        for c in self._classes:
            # Check required fields
            if c.id is None or not c.unicode or not c.character or not c.name or not c.category:
                errors.append(f"Malformed class entry: {c}")

            # Check ID uniqueness
            if c.id in seen_ids:
                duplicate_ids.append(c.id)
            seen_ids.add(c.id)

            # Check Unicode uniqueness
            if c.unicode in seen_unicodes:
                duplicate_unicodes.append(c.unicode)
            seen_unicodes.add(c.unicode)

            # Check Character uniqueness
            if c.character in seen_chars:
                duplicate_chars.append(c.character)
            seen_chars.add(c.character)

        if duplicate_ids:
            errors.append(f"Duplicate class IDs detected: {set(duplicate_ids)}")
        if duplicate_unicodes:
            errors.append(f"Duplicate Unicode code points detected: {set(duplicate_unicodes)}")
        if duplicate_chars:
            errors.append(f"Duplicate characters detected: {set(duplicate_chars)}")

        # 2. Check contiguity (0 to N-1)
        n = len(self._classes)
        expected_ids = set(range(n))
        missing_ids = expected_ids - seen_ids
        unexpected_ids = seen_ids - expected_ids

        if missing_ids:
            errors.append(f"Missing contiguous class IDs in range 0..{n-1}: {sorted(missing_ids)}")
        if unexpected_ids:
            errors.append(f"Out-of-range class IDs detected: {sorted(unexpected_ids)}")

        # 3. Cross-file consistency check with config/classes.yaml
        if self.config_path and self.config_path.exists():
            try:
                cfg = load_yaml(self.config_path)
                meta_count = cfg.get("metadata", {}).get("total_classes")
                if meta_count is not None and meta_count != n:
                    errors.append(
                        f"Mismatch between config/classes.yaml (total_classes={meta_count}) "
                        f"and corpus/charset.json (total_classes={n})"
                    )

                categories_cfg = cfg.get("categories", {})
                for cat_name, cat_info in categories_cfg.items():
                    actual_count = len(self._category_to_classes.get(cat_name, []))
                    expected_count = cat_info.get("count")
                    if expected_count is not None and actual_count != expected_count:
                        errors.append(
                            f"Category count mismatch for '{cat_name}': "
                            f"classes.yaml specifies {expected_count}, but charset.json has {actual_count}"
                        )
            except Exception as e:
                warnings.append(f"Could not verify cross-file config: {e}")

        is_valid = len(errors) == 0

        validation_report = {
            "is_valid": is_valid,
            "total_classes": n,
            "categories": {k: len(v) for k, v in self._category_to_classes.items()},
            "errors": errors,
            "warnings": warnings,
        }

        if not is_valid:
            logger.error(f"Charset validation FAILED with {len(errors)} error(s): {errors}")
        else:
            logger.info(f"Charset validation PASSED (total {n} classes verified contiguous & unique).")

        return validation_report
