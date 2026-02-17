"""
Download GitHub logo (Octocat / mark) and create assets/icon.ico for the .exe.
Run once: pip install Pillow requests && python build_icon.py
"""
import io
import os
import sys

try:
    import requests
    from PIL import Image, ImageDraw
except ImportError:
    print("Install: pip install Pillow requests")
    sys.exit(1)

# Try several possible URLs for GitHub logo (Octocat / mark)
LOGO_URLS = [
    "https://github.githubassets.com/images/modules/logos_page/Octocat.png",
    "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
    "https://raw.githubusercontent.com/github/explore/80688e429a7d4ef2fca1e82350fe8e3517d3494d/topics/github/github.png",
]
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")
ICO_SIZES = [(256, 256), (48, 48), (32, 32), (16, 16)]


def download_image():
    for url in LOGO_URLS:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and r.content:
                return Image.open(io.BytesIO(r.content)).convert("RGBA")
        except Exception:
            continue
    return None


def make_fallback_icon():
    """GitHub-style: white octocat silhouette on dark background."""
    size = 256
    img = Image.new("RGBA", (size, size), (34, 34, 34, 255))
    draw = ImageDraw.Draw(img)
    # Outer circle (GitHub mark style)
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 255, 255, 255))
    # Simple cat ears (two triangles) to suggest Octocat
    cx = size // 2
    top = margin + (size - 2 * margin) // 4
    w = (size - 2 * margin) // 3
    draw.polygon([(cx - w, top + w), (cx, top), (cx + w, top + w)], fill=(34, 34, 34, 255))
    return img


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    img = download_image()
    if img is None:
        print("Download failed, creating fallback GitHub-style icon...")
        img = make_fallback_icon()
    else:
        print("Downloaded GitHub logo.")
    img.save(ICO_PATH, format="ICO", sizes=ICO_SIZES)
    print("Saved:", ICO_PATH)


if __name__ == "__main__":
    main()
