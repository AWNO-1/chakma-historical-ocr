"""
End-to-end pipeline sanity tests for Stage 01.
Verifies config loading, seed reproducibility, directory resolution, and deterministic reconstruction.
"""

import pytest
import random
import numpy as np
import torch
from utils.file_utils import get_project_root, load_yaml, resolve_path
from utils.seed import set_seed
from utils.geometry import BBox
from inference.reconstruct_text import DeterministicTextReconstructor


def test_directory_structure_integrity():
    root = get_project_root()
    required_dirs = [
        "corpus",
        "config",
        "fonts",
        "data/backgrounds/paper",
        "data/backgrounds/parchment",
        "data/backgrounds/manuscript",
        "data/backgrounds/bamboo",
        "data/backgrounds/miscellaneous",
        "data/synthetic/images",
        "data/synthetic/labels",
        "data/real/images",
        "data/real/labels",
        "generator",
        "training",
        "inference",
        "debug",
        "utils",
        "tests",
        "docs/stages",
        "docs/decisions",
        "docs/experiments",
        "experiments",
    ]
    for d in required_dirs:
        p = root / d
        assert p.exists() and p.is_dir(), f"Required directory missing: {d}"


def test_config_files_exist_and_valid():
    configs = [
        "config/project.yaml",
        "config/classes.yaml",
        "config/synthetic.yaml",
        "config/training.yaml",
    ]
    for cfg in configs:
        data = load_yaml(cfg)
        assert isinstance(data, dict), f"Config {cfg} is not a valid YAML dictionary."
        assert len(data) > 0, f"Config {cfg} is empty."


def test_seed_reproducibility():
    set_seed(1234)
    val_py_1 = random.random()
    val_np_1 = np.random.rand()
    val_torch_1 = torch.rand(1).item()

    set_seed(1234)
    val_py_2 = random.random()
    val_np_2 = np.random.rand()
    val_torch_2 = torch.rand(1).item()

    assert val_py_1 == val_py_2
    assert val_np_1 == val_np_2
    assert val_torch_1 == val_torch_2


def test_deterministic_reconstruction_pipeline():
    id_map = {0: "𑄇", 1: "𑄈", 2: "𑄉"}
    reconstructor = DeterministicTextReconstructor(id_to_char=id_map)

    boxes = [
        BBox(x_min=100, y_min=20, x_max=120, y_max=40, class_id=2),  # 3rd char
        BBox(x_min=20, y_min=20, x_max=40, y_max=40, class_id=0),    # 1st char
        BBox(x_min=60, y_min=20, x_max=80, y_max=40, class_id=1),    # 2nd char
    ]

    doc = reconstructor.reconstruct(boxes)
    assert doc.total_characters == 3
    assert doc.full_text == "𑄇𑄈𑄉"
