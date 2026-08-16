"""
Training and Evaluation Package for Chakma Character Detection.
"""

from training.dataset_adapter import DatasetAdapter
from training.train_synthetic import run_training
from training.validate import validate_model
from training.evaluate import evaluate_splits

__all__ = [
    "DatasetAdapter",
    "run_training",
    "validate_model",
    "evaluate_splits",
]
