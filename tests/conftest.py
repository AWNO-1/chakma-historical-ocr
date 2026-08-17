"""
Pytest configuration and environment setup for Chakma Historical OCR test suite.
"""

import os
# Prevent OpenMP duplicate runtime collision between PyTorch MKL and OpenCV on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
