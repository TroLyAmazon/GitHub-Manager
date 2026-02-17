"""
Download GitHub Octocat (white cat) and create assets/icon.ico for the .exe.
Run once: pip install Pillow requests && python build_icon.py
"""
import io
import os
import sys

try:
    import requests
    from PIL import Image
except ImportError as e:
    print("Install: pip install Pillow requests")
    sys.exit(1)

OCTOCAT_URL = "https://github.githubassets.com/images/modules/logos_page/Octocat.png"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")
ICO_SIZES = (256, 48, 32, 16)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("Downloading GitHub Octocat...")
    r = requests.get(OCTOCAT_URL, timeout=15)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img.save(ICO_PATH, format="ICO", sizes=ICO_SIZES)
    print("Saved:", ICO_PATH)


if __name__ == "__main__":
    main()
