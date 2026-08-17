"""
Probe font inspection tools (fontTools, Pillow ImageFont, etc.)
"""
import sys

def probe():
    print("Python version:", sys.version)
    try:
        import fontTools
        print("fontTools available:", fontTools.__version__)
    except ImportError:
        print("fontTools not installed.")

    try:
        from PIL import ImageFont
        print("Pillow ImageFont available:", ImageFont)
    except ImportError:
        print("PIL ImageFont not installed.")

if __name__ == "__main__":
    probe()
