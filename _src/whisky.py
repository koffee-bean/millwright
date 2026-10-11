"""Build the unlisted whisky shelf page at /whisky/ (Griffin's Loot).

This page is deliberately kept out of the main build: it has no file in
_src/content/, so build.py never adds it to the nav, sitemap.xml, or llms.txt,
and IndexNow (which only submits sitemap URLs) never sends it. The page itself
carries a noindex, nofollow robots tag. Nothing on the site links to it.

  python3 _src/whisky.py                     rebuild whisky/index.html from _src/whisky/data.json
  python3 _src/whisky.py --import <folder>   refresh data and photos from a griffins-loot folder
                                             (data.json, img/<id>.jpg, pets/), then rebuild

Importing keeps only the catalog fields and re-encodes every photo, which drops
camera metadata. Needs Pillow for --import only.
"""
import datetime
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_src" / "whisky" / "data.json"
OUT = ROOT / "whisky"
KEEP = ("id", "name", "country", "region", "state", "style", "age", "age_note", "abv", "size", "notes")
# Source portrait file names on the Mac mini, mapped to the dog they show.
PETS = {"20220714_111715": "griffin", "20220714_111609": "blu"}


def import_from(src):
    from PIL import Image, ImageOps
    src = Path(src)
    raw = json.loads((src / "data.json").read_text(encoding="utf-8"))
    bottles = [{k: b[k] for k in KEEP if b.get(k) not in (None, "")} for b in raw["bottles"]]
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    (OUT / "pets").mkdir(parents=True, exist_ok=True)
    for b in bottles:
        im = ImageOps.exif_transpose(Image.open(src / "img" / f"{b['id']}.jpg")).convert("RGB")
        im.thumbnail((600, 900))
        im.save(OUT / "img" / f"{b['id']}.webp", "WEBP", quality=80, method=6)
    for stem, name in PETS.items():
        im = ImageOps.exif_transpose(Image.open(src / "pets" / f"{stem}.jpg")).convert("RGB")
        full = im.copy()
        full.thumbnail((1000, 1000))
        full.save(OUT / "pets" / f"{name}.webp", "WEBP", quality=80, method=6)
        side = min(im.size)
        sq = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2))
        sq.resize((240, 240), Image.LANCZOS).save(OUT / "pets" / f"{name}-sm.webp", "WEBP", quality=82, method=6)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps({"updated": raw["updated"], "bottles": bottles}, indent=1, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"imported {len(bottles)} bottles and {len(PETS)} portraits")


# The page template: its own warm, woody styles, independent of assets/site.css.
PAGE_TEMPLATE = ROOT / "_src" / "whisky" / "page.html"


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    whisky = [b for b in data["bottles"] if b["region"] != "Not whisky"]
    aged = [b for b in whisky if b.get("age")]
    stats = [(len(whisky), "Whiskies"), (len({b["country"] for b in whisky}), "Countries"),
             (len(aged), "With an age statement")]
    if aged:
        stats.append((max(b["age"] for b in aged), "Years, the oldest"))
    updated = datetime.date.fromisoformat(data["updated"]).strftime("%B %-d, %Y")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (PAGE_TEMPLATE.read_text(encoding="utf-8")
                .replace("__STATS__", "".join(f"<li><b>{n}</b><span>{label}</span></li>" for n, label in stats))
                .replace("__UPDATED__", html.escape(updated))
                .replace("__DATA__", payload))
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"built whisky/index.html: {len(data['bottles'])} bottles ({len(whisky)} whiskies)")


if __name__ == "__main__":
    if "--import" in sys.argv:
        import_from(sys.argv[sys.argv.index("--import") + 1])
    build()
