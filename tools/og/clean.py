"""Re-save each /og/*.png with nothing but its pixels: no text chunks, no tool names."""
from pathlib import Path
from PIL import Image

for f in sorted((Path(__file__).resolve().parents[2] / "og").glob("*.png")):
    img = Image.open(f).convert("RGB")
    img.save(f, "PNG", optimize=True)
    print(f.name, f.stat().st_size // 1024, "KB")
