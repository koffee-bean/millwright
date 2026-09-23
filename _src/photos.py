"""Turn the Unsplash originals in _src/photos/ into the site's tinted WebP images.

Every photo gets the same treatment so the set reads as one family: colour pulled
back toward neutral, then a light tritone: deep navy shadows, warm sand
midtones, cream highlights. Output: assets/img/<name>.webp (1200x900) and <name>-sm.webp (720x540).

Run: python3 _src/photos.py   (needs Pillow)
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "_src" / "photos", ROOT / "assets" / "img"
SHADOW, MID, HIGHLIGHT = (31, 45, 69), (178, 168, 152), (250, 246, 238)

# Horizontal focal point (0 = left edge, 1 = right edge) for the 4:3 crop.
FOCUS = {
    "industry-healthcare": .62, "industry-hospitality": .4, "industry-saas": .36,
    "service-retainer": .62, "service-diagnostic": .45, "work-health-data-foundation": .78,
    "work-hospitality-governance": .55, "writing-hub": .55, "writing-is-our-data-ready-for-ai": .3,
    "writing-why-is-our-snowflake-bill-so-high": .45,
}
# Photos that arrive very saturated get pulled back further.
LOUD = {"industry-semiconductor", "writing-why-is-our-snowflake-bill-so-high",
        "writing-do-we-need-a-semantic-layer-before-ai", "work-games-metadata-catalog", "services-hub", "industry-saas"}


def crop43(im, fx):
    w, h = im.size
    if w / h > 4 / 3:
        nw = round(h * 4 / 3)
        left = min(max(round(fx * w - nw / 2), 0), w - nw)
        return im.crop((left, 0, left + nw, h))
    nh = round(w * 3 / 4)
    top = (h - nh) // 2
    return im.crop((0, top, w, top + nh))


def treat(im, loud):
    base = ImageEnhance.Color(im).enhance(.36 if loud else .58)
    duo = ImageOps.colorize(ImageOps.autocontrast(im.convert("L"), cutoff=1), SHADOW, HIGHLIGHT, mid=MID)
    out = Image.blend(base, duo, .34)
    return ImageEnhance.Contrast(out).enhance(.96)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(SRC.glob("*.jpg")):
        name = path.stem
        im = crop43(ImageOps.exif_transpose(Image.open(path)).convert("RGB"), FOCUS.get(name, .5))
        im = treat(im, name in LOUD)
        im.resize((1200, 900), Image.LANCZOS).save(OUT / f"{name}.webp", "WEBP", quality=78, method=6)
        im.resize((720, 540), Image.LANCZOS).save(OUT / f"{name}-sm.webp", "WEBP", quality=76, method=6)
    print(f"processed {len(list(SRC.glob('*.jpg')))} photos into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
