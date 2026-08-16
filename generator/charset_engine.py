"""
Charset Engine for Chakma script character mapping and validation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
from utils.file_utils import load_json, resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("charset_engine")


class CharsetEngine:
    """
    Manages Chakma script character inventory, Unicode mappings, and YOLO class IDs.
    """

    def __init__(self, charset_path: Union[str, Path] = "corpus/charset.json"):
        self.charset_path = resolve_path(charset_path)
        self.char_to_id: Dict[str, int] = {}
        self.id_to_char: Dict[int, str] = {}
        self.classes_info: List[Dict] = []
        self._load_charset()

    def _load_charset(self) -> None:
        """Load charset definitions from JSON."""
        if not self.charset_path.exists():
            logger.warning(f"Charset file not found at: {self.charset_path}")
            return

        try:
            data = load_json(self.charset_path)
            self.classes_info = data.get("classes", [])
            for item in self.classes_info:
                cid = item.get("id")
                char = item.get("char")
                if cid is not None and char is not None:
                    self.char_to_id[char] = cid
                    self.id_to_char[cid] = char
            logger.info(f"Loaded {len(self.char_to_id)} classes from {self.charset_path}")
        except Exception as e:
            logger.error(f"Error loading charset from {self.charset_path}: {e}")

    @property
    def num_classes(self) -> int:
        return len(self.char_to_id)

    def get_class_id(self, char: str) -> Optional[int]:
        """Get class ID for a character."""
        return self.char_to_id.get(char)

    def get_char(self, class_id: int) -> Optional[str]:
        """Get character for a class ID."""
        return self.id_to_char.get(class_id)

    def is_valid_char(self, char: str) -> bool:
        """Check if character exists in charset."""
        return char in self.char_to_id
