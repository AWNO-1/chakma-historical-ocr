"""
Chakma Historical OCR - System Diagnostic & Entry Point
Performs environment check, project structure integrity validation, and configuration loading.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import torch

from utils.file_utils import get_project_root, load_yaml, resolve_path
from utils.logging_utils import setup_logger
from utils.seed import set_seed

logger = setup_logger("main")


def check_project_structure() -> Tuple[bool, List[str], List[str]]:
    """
    Validate that all essential directories and files exist.
    """
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

    required_files = [
        "corpus/sentences.txt",
        "corpus/vocabulary.txt",
        "corpus/charset.json",
        "config/project.yaml",
        "config/classes.yaml",
        "config/synthetic.yaml",
        "config/training.yaml",
        "generator/__init__.py",
        "generator/api.py",
        "generator/corpus_engine.py",
        "generator/charset_engine.py",
        "generator/font_engine.py",
        "generator/layout_engine.py",
        "generator/line_renderer.py",
        "generator/background.py",
        "generator/augmentations.py",
        "generator/transform_engine.py",
        "generator/annotation_engine.py",
        "generator/metadata.py",
        "training/__init__.py",
        "training/train_synthetic.py",
        "training/validate.py",
        "training/evaluate.py",
        "training/dataset_adapter.py",
        "inference/__init__.py",
        "inference/detect.py",
        "inference/reconstruct_text.py",
        "debug/__init__.py",
        "debug/visualize_synthetic.py",
        "debug/visualize_labels.py",
        "debug/visualize_predictions.py",
        "utils/__init__.py",
        "utils/image_utils.py",
        "utils/geometry.py",
        "utils/seed.py",
        "utils/logging_utils.py",
        "utils/file_utils.py",
        "tests/__init__.py",
        "tests/test_charset.py",
        "tests/test_corpus.py",
        "tests/test_fonts.py",
        "tests/test_geometry.py",
        "tests/test_generator.py",
        "tests/test_pipeline.py",
        "requirements.txt",
        "CHANGELOG.md",
        "README.md",
    ]

    missing_dirs = [d for d in required_dirs if not (root / d).is_dir()]
    missing_files = [f for f in required_files if not (root / f).is_file()]

    is_valid = len(missing_dirs) == 0 and len(missing_files) == 0
    return is_valid, missing_dirs, missing_files


def get_environment_info() -> Dict[str, Any]:
    """
    Collect system, Python, and hardware acceleration details.
    """
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    device_count = torch.cuda.device_count() if cuda_available else 0

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "cuda_available": cuda_available,
        "device": device_name,
        "device_count": device_count,
        "pytorch_version": torch.__version__,
    }


def get_key_dependencies() -> Dict[str, str]:
    """
    Query installed versions of core project dependencies.
    """
    packages = [
        "torch",
        "torchvision",
        "ultralytics",
        "PIL",
        "cv2",
        "yaml",
        "numpy",
        "pytest",
    ]
    installed = {}
    for pkg in packages:
        try:
            if pkg == "PIL":
                import PIL
                installed["Pillow"] = getattr(PIL, "__version__", "Installed")
            elif pkg == "cv2":
                import cv2
                installed["opencv-python"] = getattr(cv2, "__version__", "Installed")
            elif pkg == "yaml":
                import yaml
                installed["PyYAML"] = getattr(yaml, "__version__", "Installed")
            else:
                mod = __import__(pkg)
                installed[pkg] = getattr(mod, "__version__", "Installed")
        except ImportError:
            installed[pkg] = "NOT INSTALLED"
    return installed


def print_system_status() -> bool:
    """
    Print diagnostic banner and system status report.
    """
    print("=" * 70)
    print("       CHAKMA HISTORICAL OCR - SYSTEM INITIALIZATION & DIAGNOSTIC      ")
    print("=" * 70)

    # 1. Environment Info
    env = get_environment_info()
    print("\n[1] ENVIRONMENT & RUNTIME:")
    print(f"  * Operating System   : {env['os']}")
    print(f"  * Python Version     : {env['python_version']}")
    print(f"  * Python Path        : {env['python_executable']}")
    print(f"  * Compute Device     : {env['device']} (CUDA Available: {env['cuda_available']})")
    print(f"  * PyTorch Version    : {env['pytorch_version']}")

    # 2. Key Dependencies
    deps = get_key_dependencies()
    print("\n[2] KEY DEPENDENCIES:")
    for name, ver in deps.items():
        status_flag = "[OK]" if ver != "NOT INSTALLED" else "[MISSING]"
        print(f"  * {name:<18} : {ver:<15} {status_flag}")

    # 3. Configurations
    print("\n[3] CONFIGURATIONS:")
    project_cfg = load_yaml("config/project.yaml")
    seed = project_cfg.get("reproducibility", {}).get("seed", 42)
    det = project_cfg.get("reproducibility", {}).get("deterministic", True)
    set_seed(seed, deterministic=det)

    print(f"  * Project Name       : {project_cfg.get('project', {}).get('name')}")
    print(f"  * Project Version    : {project_cfg.get('project', {}).get('version')}")
    print(f"  * Central Seed       : {seed} (Deterministic: {det})")
    print(f"  * Logging Level      : {project_cfg.get('logging', {}).get('level')}")

    # 4. Structure Integrity Check
    is_valid, missing_dirs, missing_files = check_project_structure()
    print("\n[4] PROJECT REPOSITORY INTEGRITY:")
    if is_valid:
        print("  * Structure Status   : [PASSED] All directories and files verified.")
    else:
        print("  * Structure Status   : [FAILED]")
        if missing_dirs:
            print(f"    Missing Directories: {missing_dirs}")
        if missing_files:
            print(f"    Missing Files      : {missing_files}")

    print("\n" + "=" * 70)
    return is_valid


if __name__ == "__main__":
    success = print_system_status()
    if not success:
        sys.exit(1)
