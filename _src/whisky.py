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
import hashlib
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


def css_version():
    return hashlib.sha1((ROOT / "assets" / "site.css").read_bytes()).hexdigest()[:8]


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Griffin's Loot</title>
<meta name="theme-color" content="#F8F5EF">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="/favicon-64.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@100..900&display=swap">
<link rel="stylesheet" href="/assets/site.css?v=__CSSV__">
<style>
.gl-head{padding:48px 0 28px;border-bottom:1px solid var(--hairline)}
.gl-top{display:flex;justify-content:space-between;align-items:flex-end;gap:var(--s3);flex-wrap:wrap}
.gl-head h1{--h1-size:clamp(40px,5.2vw,64px)}
.gl-tag{color:var(--muted);font-size:clamp(17px,1.5vw,20px);margin:10px 0 0;max-width:46ch}
.keepers{display:flex;align-items:center;gap:16px}
.keepers .faces{display:flex}
.keepers button{appearance:none;border:0;padding:0;background:none;cursor:zoom-in;display:flex;flex-direction:column;align-items:center;gap:6px;font:inherit;color:inherit}
.keepers button+button{margin-left:-10px}
.keepers img{width:84px;height:84px;border-radius:50%;object-fit:cover;display:block;border:3px solid var(--bg);box-shadow:0 0 0 1.5px var(--accent)}
.keepers .pet{font-size:13px;font-weight:620;color:var(--muted)}
.keepers .cap{font-size:15px;line-height:1.3;color:var(--muted)}
.keepers .cap b{display:block;color:var(--ink);font-size:18px;font-weight:700}
.gl-stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:var(--s3);list-style:none;padding:0}
.gl-stats li{border:1px solid var(--hairline);background:var(--bg2);border-radius:999px;padding:6px 14px;font-size:14px;color:var(--muted)}
.gl-stats b{color:var(--ink);font-weight:680}
.controls{position:sticky;top:0;z-index:5;background:rgba(248,245,239,.94);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--hairline)}
.controls .container{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;padding-top:12px;padding-bottom:12px}
.seg{display:inline-flex;border:1px solid var(--hairline);background:var(--bg2);border-radius:999px;padding:3px}
.seg button{appearance:none;border:0;background:transparent;color:var(--muted);font:inherit;font-size:14px;font-weight:620;padding:8px 16px;border-radius:999px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
.search{flex:1 1 220px;min-width:0;position:relative}
.search input{width:100%;border:1px solid var(--hairline);background:#fff;color:var(--ink);border-radius:999px;padding:10px 16px 10px 40px;font:inherit;font-size:15px}
.search input:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
.search svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:17px;height:17px;color:var(--muted)}
.jump{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;width:100%}
.jump::-webkit-scrollbar{display:none}
.jump a{flex:none;color:var(--muted);font-size:13px;border:1px solid var(--hairline);border-radius:999px;padding:5px 11px;text-decoration:none}
.jump a:hover{color:var(--accent);border-color:var(--accent);text-decoration:none}
.jump span{opacity:.6}
.group{padding:var(--s4) 0 var(--s1);scroll-margin-top:130px}
.group-head{display:flex;align-items:baseline;gap:12px;margin:0 0 var(--s2);border-bottom:1px solid var(--hairline);padding-bottom:10px}
.group-head h2{font-size:clamp(24px,2.4vw,30px)}
.group-head .sub{color:var(--muted);font-size:15px}
.group-head .count{margin-left:auto;color:var(--accent);font-weight:680;font-size:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
@media (min-width:720px){.grid{grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:18px}}
.bottle{appearance:none;text-align:left;font:inherit;color:inherit;padding:0;background:var(--bg);border:1px solid var(--hairline);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;cursor:pointer;transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease}
.bottle:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:0 10px 24px rgba(27,27,25,.06)}
.bottle:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.shot{background:#fff;aspect-ratio:2/3;position:relative;display:grid;place-items:center}
.shot img{width:100%;height:100%;object-fit:contain;display:block}
.age{position:absolute;top:8px;left:8px;background:var(--accent);color:#fff;font-size:12px;font-weight:680;padding:3px 9px;border-radius:999px}
.age.nas{background:var(--bg2);color:var(--muted);border:1px solid var(--hairline)}
.meta{padding:10px 12px 13px;display:flex;flex-direction:column;gap:3px;border-top:1px solid var(--hairline)}
.meta .nm{font-weight:650;font-size:15px;line-height:1.3}
.meta .facts{color:var(--muted);font-size:13px;line-height:1.4}
.empty{color:var(--muted);padding:var(--s5) 0;text-align:center}
dialog{border:1px solid var(--hairline);border-radius:16px;padding:0;background:var(--bg);color:var(--ink);width:min(760px,calc(100vw - 24px));max-height:calc(100dvh - 24px)}
dialog::backdrop{background:rgba(27,27,25,.55)}
.dlg{display:grid;grid-template-columns:1fr}
@media (min-width:640px){.dlg{grid-template-columns:280px 1fr}}
.dlg .shot{aspect-ratio:auto;min-height:320px}
.dlg .body{padding:22px 24px 24px;display:flex;flex-direction:column;gap:14px}
.dlg h3{font-size:24px;font-weight:720;letter-spacing:-.015em;line-height:1.2;padding-right:36px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:7px 16px;font-size:15px;margin:0}
.kv dt{color:var(--muted);font-size:12px;font-weight:660;letter-spacing:.08em;text-transform:uppercase;padding-top:2px}
.kv dd{margin:0}
.pet-view img{width:100%;display:block}
.close{position:absolute;top:10px;right:10px;width:36px;height:36px;border-radius:999px;border:1px solid var(--hairline);background:var(--bg);color:var(--ink);font-size:20px;line-height:1;cursor:pointer;z-index:1}
.gl-foot{color:var(--muted);font-size:13px;text-align:center;padding:var(--s5) 16px var(--s4)}
@media (max-width:520px){.keepers img{width:64px;height:64px}.gl-head{padding-top:32px}.container{padding:0 16px}}
@media (prefers-reduced-motion:reduce){.bottle{transition:none}.bottle:hover{transform:none}}
</style>
</head>
<body>
<header class="gl-head">
  <div class="container">
    <div class="gl-top">
      <div>
        <span class="eyebrow">The shelf</span>
        <h1>Griffin's Loot</h1>
        <p class="gl-tag">Every bottle on our shelf, by region and by age.</p>
      </div>
      <div class="keepers">
        <div class="faces">
          <button type="button" data-pet="griffin" data-name="Griffin"><img src="pets/griffin-sm.webp" width="240" height="240" alt="Griffin, our Yorkie"><span class="pet">Griffin</span></button>
          <button type="button" data-pet="blu" data-name="Blu"><img src="pets/blu-sm.webp" width="240" height="240" alt="Blu, our French bulldog"><span class="pet">Blu</span></button>
        </div>
        <div class="cap">Guarded by<b>Griffin &amp; Blu</b></div>
      </div>
    </div>
    <ul class="gl-stats">__STATS__</ul>
  </div>
</header>

<div class="controls">
  <div class="container">
    <div class="seg" role="group" aria-label="Group bottles by">
      <button type="button" data-mode="region" aria-pressed="true">By region</button>
      <button type="button" data-mode="age" aria-pressed="false">By age</button>
    </div>
    <label class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="Search bottles, regions, styles" autocomplete="off" aria-label="Search bottles">
    </label>
    <nav class="jump" id="jump" aria-label="Jump to group"></nav>
  </div>
</div>

<main class="container" id="list" aria-live="polite"></main>
<footer class="gl-foot">Catalogued __UPDATED__ from shelf photos.</footer>

<dialog id="dlg" aria-labelledby="dlg-title">
  <button class="close" type="button" aria-label="Close" data-close>&times;</button>
  <div class="dlg" id="dlg-body"></div>
</dialog>

<script type="application/json" id="data">__DATA__</script>
<script>
const REGIONS = [["Speyside","Scotland"],["Highlands","Scotland"],["Lowlands","Scotland"],["Islands","Scotland"],
  ["Blended Scotch","Scotland"],["England",""],["Ireland",""],["Japan",""],["New Zealand",""],
  ["Kentucky","USA"],["Tennessee","USA"],["Washington","USA"],["Other USA","USA"],["Not whisky","Also on the shelf"]];
const AGES = [["15+ years",b=>b.age>=15],["10 to 14 years",b=>b.age>=10&&b.age<15],["Under 10 years",b=>b.age&&b.age<10],["No age statement",b=>!b.age]];
const DATA = JSON.parse(document.getElementById("data").textContent).bottles;
const get = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const put = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
let mode = get("gl-mode") === "age" ? "age" : "region";
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const isWhisky = b => b.region !== "Not whisky";
const place = b => b.region === "Other USA" ? b.state : b.region;
const byAge = (a, b) => (b.age || 0) - (a.age || 0) || a.name.localeCompare(b.name);

const card = b => `<button class="bottle" type="button" data-id="${esc(b.id)}">
  <div class="shot"><img loading="lazy" src="img/${esc(b.id)}.webp" width="600" height="900" alt="${esc(b.name)}">
    <span class="age${b.age ? "" : " nas"}">${b.age ? b.age + " yr" : "NAS"}</span></div>
  <div class="meta"><span class="nm">${esc(b.name)}</span><span class="facts">${esc([place(b), b.style].filter(Boolean).join(" · "))}</span></div>
</button>`;

function render() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  const rows = DATA.filter(b => !q || [b.name, b.region, b.country, b.style, b.state, b.notes].join(" ").toLowerCase().includes(q));
  let groups;
  if (mode === "region") {
    groups = REGIONS.map(([r, sub]) => ({ title: r, sub, rows: rows.filter(b => b.region === r).sort(byAge) }));
  } else {
    groups = AGES.map(([t, f]) => ({ title: t, sub: "", rows: rows.filter(b => isWhisky(b) && f(b)).sort(byAge) }));
    groups.push({ title: "Also on the shelf", sub: "Not whisky", rows: rows.filter(b => !isWhisky(b)) });
  }
  groups = groups.filter(g => g.rows.length);
  document.getElementById("jump").innerHTML = groups.map(g => `<a href="#g-${slug(g.title)}">${esc(g.title)} <span>${g.rows.length}</span></a>`).join("");
  document.getElementById("list").innerHTML = groups.length ? groups.map(g => `<section class="group" id="g-${slug(g.title)}">
    <div class="group-head"><h2>${esc(g.title)}</h2>${g.sub ? `<span class="sub">${esc(g.sub)}</span>` : ""}<span class="count">${g.rows.length}</span></div>
    <div class="grid">${g.rows.map(card).join("")}</div></section>`).join("")
    : `<p class="empty">No bottles match &ldquo;${esc(q)}&rdquo;.</p>`;
}

function show(b) {
  const where = b.region === "Other USA" ? `${b.state}, USA` : (b.region === b.country || b.region === "Not whisky" ? b.country : `${b.region}, ${b.country}`);
  const age = (b.age ? `${b.age} years` : "No age statement") + (b.age_note ? ` (${b.age_note})` : "");
  const kv = [["Region", where], ["Style", b.style], ["Age", age], ["Strength", b.abv], ["Size", b.size], ["Notes", b.notes]].filter(r => r[1]);
  document.getElementById("dlg-body").innerHTML = `<div class="shot"><img src="img/${esc(b.id)}.webp" alt="${esc(b.name)}"></div>
    <div class="body"><h3 id="dlg-title">${esc(b.name)}</h3><dl class="kv">${kv.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl></div>`;
  document.getElementById("dlg").showModal();
}

document.addEventListener("click", e => {
  const pet = e.target.closest("[data-pet]");
  if (pet) {
    document.getElementById("dlg-body").innerHTML = `<div class="pet-view" style="grid-column:1/-1"><img src="pets/${pet.dataset.pet}.webp" alt="${esc(pet.dataset.name)}"><div class="body"><h3 id="dlg-title">${esc(pet.dataset.name)}</h3></div></div>`;
    document.getElementById("dlg").showModal(); return;
  }
  const c = e.target.closest(".bottle"); if (c) { show(DATA.find(b => b.id === c.dataset.id)); return; }
  if (e.target.closest("[data-close]") || e.target.id === "dlg") { document.getElementById("dlg").close(); return; }
  const m = e.target.closest(".seg button");
  if (m) { mode = m.dataset.mode; put("gl-mode", mode); document.querySelectorAll(".seg button").forEach(x => x.setAttribute("aria-pressed", x === m)); render(); }
});
document.getElementById("q").addEventListener("input", render);
document.querySelectorAll(".seg button").forEach(x => x.setAttribute("aria-pressed", x.dataset.mode === mode));
render();
</script>
</body>
</html>
"""


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    whisky = [b for b in data["bottles"] if b["region"] != "Not whisky"]
    aged = [b for b in whisky if b.get("age")]
    stats = [f"<b>{len(whisky)}</b> whiskies", f"<b>{len({b['country'] for b in whisky})}</b> countries",
             f"<b>{len(aged)}</b> with an age statement"]
    if aged:
        stats.append(f"Oldest <b>{max(b['age'] for b in aged)} yr</b>")
    updated = datetime.date.fromisoformat(data["updated"]).strftime("%B %-d, %Y")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (PAGE.replace("__CSSV__", css_version())
                .replace("__STATS__", "".join(f"<li>{s}</li>" for s in stats))
                .replace("__UPDATED__", html.escape(updated))
                .replace("__DATA__", payload))
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"built whisky/index.html: {len(data['bottles'])} bottles ({len(whisky)} whiskies)")


if __name__ == "__main__":
    if "--import" in sys.argv:
        import_from(sys.argv[sys.argv.index("--import") + 1])
    build()
