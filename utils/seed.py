"""
Seed and reproducibility utilities for Chakma Historical OCR.
"""

import os
import random
import numpy as np
import torch
from typing import Optional


def set_seed(seed: int = 42, deterministic: bool = True) -> int:
    """
    Set central random seed across Python random, NumPy, and PyTorch for full reproducibility.

    Args:
        seed: The integer seed value.
        deterministic: If True, forces deterministic algorithms in PyTorch and cuDNN.

    Returns:
        The integer seed applied.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    return seed
