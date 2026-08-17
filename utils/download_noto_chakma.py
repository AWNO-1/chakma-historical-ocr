"""
Download official Noto Sans Chakma open-source font if internet connection is available.
"""
import urllib.request
from pathlib import Path

def download_noto():
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)
    target = fonts_dir / "NotoSansChakma-Regular.ttf"
    
    url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansChakma/NotoSansChakma-Regular.ttf"
    try:
        print(f"Downloading NotoSansChakma-Regular.ttf from Google Fonts repo...")
        urllib.request.urlretrieve(url, target)
        print(f"Downloaded successfully: {target} ({target.stat().st_size} bytes)")
    except Exception as e:
        print(f"Could not download Noto font: {e}")

if __name__ == "__main__":
    download_noto()
