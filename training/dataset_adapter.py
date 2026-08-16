"""
Dataset adapter utilities for preparing YOLO dataset config yaml and directory splits.
"""

from pathlib import Path
from typing import Dict, Union
from utils.file_utils import resolve_path, save_yaml, ensure_dir
from utils.logging_utils import setup_logger

logger = setup_logger("dataset_adapter")


class DatasetAdapter:
    """
    Constructs YOLO-compatible dataset configuration files (dataset.yaml).
    """

    @staticmethod
    def create_yolo_dataset_yaml(
        dataset_root: Union[str, Path],
        train_path: str,
        val_path: str,
        test_path: str,
        class_names: Dict[int, str],
        output_yaml_path: Union[str, Path],
    ) -> Path:
        """
        Generate dataset.yaml for Ultralytics YOLO training.
        """
        root = resolve_path(dataset_root)
        out_path = resolve_path(output_yaml_path)

        data = {
            "path": str(root).replace("\\", "/"),
            "train": train_path,
            "val": val_path,
            "test": test_path,
            "names": {int(k): v for k, v in class_names.items()},
        }

        save_yaml(data, out_path)
        logger.info(f"Generated YOLO dataset config at: {out_path}")
        return out_path
