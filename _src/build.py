#!/usr/bin/env python3
"""Build the Millwright Data site.

Reads page content from _src/content/<section>/<slug>.html, wraps each file in
the shared layout, and writes the finished pages to /<section>/<slug>/index.html
at the repository root. It also builds the four section index pages, keeps
sitemap.xml and llms.txt in sync with every page, and refreshes the case-study
and writing lists on the home page between their build markers.

Standard library only. Run from anywhere:

    python3 _src/build.py
"""
import datetime
import hashlib
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
SITE = "https://millwrightdata.com"
CAL = "https://cal.com/millwright-data"
LINKEDIN = "https://www.linkedin.com/in/srivastava-sid"
# The post shown under "Latest from LinkedIn" on /writing/. Paste the activity number
# from a new post's URL here and rebuild to change it.
LINKEDIN_POST = "7507253132435902464"
TODAY = datetime.date.today().isoformat()

SECTIONS = {
    "services": {
        "nav": "Services",
        "title": "Services",
        "eyebrow": "Services",
        "h1": "Four ways to work together",
        "lede": "A fast diagnostic, a build with a defined finish line, standing advice, or a data leader in the room before you are ready to hire one. Each one ends with the machinery running in your accounts and your team able to own it.",
        "description": "Data platform, governance, and AI services from Millwright Data: a two-week diagnostic, fixed-scope builds, monthly advisory, and a fractional head of data.",
    },
    "industries": {
        "nav": "Industries",
        "title": "Industries",
        "eyebrow": "Industries",
        "h1": "Seven industries. One discipline.",
        "lede": "Every industry here has different regulators, data volumes, and ideas about what done means. What carries across is the platform work underneath. These pages cover what is different about each one.",
        "description": "How Millwright Data approaches data platforms, governance, and AI in semiconductor, healthcare, hospitality, games, SaaS, compliance, and utilities.",
    },
    "work": {
        "nav": "Case studies",
        "title": "Case studies",
        "eyebrow": "Case studies",
        "h1": "Selected work",
        "lede": "Four platforms I led, what was broken when I arrived, and what changed. They come from roles I held before founding Millwright Data, so company names are withheld and every figure is one I can stand behind.",
        "description": "Case studies from Sid Srivastava: a metadata catalog across 70,000 datasets, the data foundation behind a $425M acquisition, ML pipelines at 99.8% uptime, and a governance model a resort company used.",
    },
    "writing": {
        "nav": "Writing",
        "title": "Writing",
        "eyebrow": "Writing",
        "h1": "Straight answers to the questions buyers ask",
        "lede": "Each piece starts with the question as you would type it, answers it in the first two sentences, then goes as deep as the problem needs.",
        "description": "Articles from Sid Srivastava on data platform cost, semantic layers, AI readiness, and when to bring in a fractional head of data.",
    },
}
ORDER = ["services", "industries", "work", "writing"]

LAYOUT = (SRC / "layout.html").read_text(encoding="utf-8")


def chrome():
    """The home page is the single source for shared chrome: flag sprite, header
    flags, footer, and service icons. Pull them from it on every build so inner
    pages can never drift from it."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    grab = lambda pat: re.search(pat, home, re.S).group(0)
    sprite = grab(r'<svg width="0" height="0" style="position:absolute".*?</svg>')
    flags = grab(r'<span class="hdr-flags">.*?</button>\s*</span>')
    footer = grab(r"<footer>.*?</footer>")
    footer = re.sub(r'src="data:image/png;base64,[^"]+"', 'src="/assets/wordmark.png"', footer)
    footer = re.sub(r'\s*<p class="legal"><sup class="fn">1</sup>.*?</p>', "", footer, flags=re.S)  # logo footnote only applies on the home page
    footer = footer.replace('href="#top"', 'href="/"').replace('href="privacy.html"', 'href="/privacy.html"')
    icons = {}
    for svg, name in re.findall(r'<span class="wb-ico" aria-hidden="true">(<svg.*?</svg>)</span><h3 class="wb-tier">(?:<a [^>]*>)?([^<]+)', home, re.S):
        icons[re.sub(r"[^a-z]+", "-", name.lower()).strip("-")] = svg
    return sprite, flags, footer, icons


SPRITE, FLAGS, FOOTER, ICONS = chrome()


# ---------------------------------------------------------------- content
def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->\s*(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"{path}: missing metadata comment")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    meta["body"] = m.group(2).strip()
    meta["slug"] = path.stem
    meta["section"] = path.parent.name
    meta["url"] = f"/{meta['section']}/{meta['slug']}/"
    meta["order"] = int(meta.get("order", 99))
    for need in ("title", "description", "summary"):
        if not meta.get(need):
            raise SystemExit(f"{path}: missing '{need}'")
    return meta


def pairs(value):
    """'A=B|C=D' -> [('A','B'), ('C','D')]"""
    out = []
    for item in (value or "").split("|"):
        if "=" in item:
            k, _, v = item.partition("=")
            out.append((k.strip(), v.strip()))
    return out


def words(html_text):
    return len(re.sub(r"<[^>]+>", " ", html_text).split())


def esc(text):
    return html.escape(text, quote=True)


def load():
    pages = {}
    for section in ORDER:
        folder = SRC / "content" / section
        items = [parse(p) for p in sorted(folder.glob("*.html"))]
        pages[section] = sorted(items, key=lambda p: (p["order"], p["title"]))
    return pages


# ---------------------------------------------------------------- pieces
def nav(active):
    rows = []
    for section in ORDER:
        cur = ' aria-current="page"' if section == active else ""
        rows.append(f'      <a href="/{section}/"{cur}>{SECTIONS[section]["nav"]}</a>')
    rows.append('      <a href="/#contact">Contact</a>')
    return "\n".join(rows)


def crumbs(trail):
    parts = ['<a href="/">Home</a>']
    for label, href in trail[:-1]:
        parts.append(f'<a href="{href}">{esc(label)}</a>')
    parts.append(f'<span aria-current="page">{esc(trail[-1][0])}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + "<span>/</span>".join(parts) + "</nav>"


def breadcrumb_ld(trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
    for i, (label, href) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": label, "item": SITE + href})
    return {"@type": "BreadcrumbList", "itemListElement": items}


AUTHOR = {"@type": "Person", "@id": SITE + "/#sid", "name": "Sid Srivastava", "url": SITE + "/",
          "sameAs": ["https://www.linkedin.com/in/srivastava-sid", "https://github.com/koffee-bean"]}
PUBLISHER = {"@type": "Organization", "@id": SITE + "/#llc", "name": "Millwright Data",
             "logo": {"@type": "ImageObject", "url": SITE + "/icon-512.png"}}


def jsonld(*nodes):
    doc = {"@context": "https://schema.org", "@graph": list(nodes)}
    return '<script type="application/ld+json">\n' + json.dumps(doc, indent=1, ensure_ascii=False) + "\n</script>"


def glance(items, extra=""):
    rows = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in items)
    return f'<aside class="aside-box"><dl>{rows}</dl>{extra}</aside>'


def book_btn(label="Book a call"):
    return f'<a class="btn" href="{CAL}" target="_blank" rel="noopener">{label}</a>'


def closing(heading, text):
    return f"""<section class="cta-close band">
  <div class="container">
    <div class="box">
      <div><h2>{esc(heading)}</h2><p>{esc(text)}</p></div>
      {book_btn()}
    </div>
  </div>
</section>"""


def render(page_meta, body, section, jsonld_nodes, og_type="website"):
    title = page_meta["title_tag"]
    out = LAYOUT
    for key, value in {
        "title": esc(title),
        "og_title": esc(title),
        "description": esc(page_meta["description"]),
        "canonical": SITE + page_meta["url"],
        "og_type": og_type,
        "jsonld": jsonld(*jsonld_nodes),
        "sprite": SPRITE,
        "flags": FLAGS,
        "footer": FOOTER,
        "nav": nav(section),
        "body": body,
    }.items():
        out = out.replace("{{" + key + "}}", value)
    if "{{" in out:
        raise SystemExit(f"unfilled placeholder in {page_meta['url']}: " + re.search(r"\{\{\w+\}\}", out).group(0))
    return out


def asset_versions(text):
    """Stamp /assets/site.css and site.js with a short content hash, so browsers
    fetch the new file after every change instead of a cached copy."""
    for name in ("site.css", "site.js"):
        digest = hashlib.sha1((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]
        text = re.sub(rf'/assets/{re.escape(name)}(\?v=\w+)?"', f'/assets/{name}?v={digest}"', text)
    return text


def write(url, text):
    target = ROOT / url.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(asset_versions(text), encoding="utf-8")


def lookup(pages, section, slug):
    return next((p for p in pages[section] if p["slug"] == slug), None)


PHOTO_PREFIX = {"services": "service", "industries": "industry", "work": "work", "writing": "writing"}


# Alt text for every photo in assets/img. The build stops if a photo has none.
PHOTO_ALT = {
    "industry-compliance": "A hand signing a printed document with a fountain pen",
    "industry-games": "A black game controller on a white surface",
    "industry-healthcare": "A stethoscope on a white desk beside a small potted succulent",
    "industry-hospitality": "A made hotel bed with white linen beside a tall window",
    "industry-saas": "A laptop and a pair of glasses on a wooden desk, seen from above",
    "industry-semiconductor": "Close-up of a silicon wafer showing rows of chips",
    "industry-utilities": "Electricity pylons and power lines under a pale sky",
    "service-build": "A pencil and a scale ruler resting on a technical drawing",
    "service-diagnostic": "A magnifying glass, a notepad, and a pencil on a white desk",
    "service-head-of-data": "A leather notebook, a spiral notepad, and a pen on a concrete desk",
    "service-retainer": "An open monthly planner with a pen and a sticky note",
    "work-games-metadata-catalog": "Close-up of the face buttons on a game controller",
    "work-health-data-foundation": "Three amber supplement bottles on a light surface",
    "work-hospitality-governance": "A long, quiet hotel corridor",
    "work-semiconductor-ml-pipelines": "Close-up of a dark circuit board with gold contacts",
    "writing-why-is-our-snowflake-bill-so-high": "A calculator and a white pen on a desk",
    "writing-do-we-need-a-semantic-layer-before-ai": "Sheets of paper fanned out in overlapping layers",
    "writing-when-to-hire-a-fractional-head-of-data": "An empty desk and chair between two tall windows",
    "writing-is-our-data-ready-for-ai": "A clipboard holding a bulleted list, beside a pen and a laptop",
}


def photo_name(section, slug=None):
    """assets/img/<name>.webp for a page, or None if there is no photo."""
    name = f"{section}-hub" if slug is None else f"{PHOTO_PREFIX[section]}-{slug}"
    return name if (ROOT / "assets" / "img" / f"{name}.webp").exists() else None


def thumb(p):
    name = photo_name(p["section"], p["slug"])
    if not name:
        return ""
    if name not in PHOTO_ALT:
        raise SystemExit(f"assets/img/{name}.webp has no alt text. Add it to PHOTO_ALT in _src/build.py")
    return (f'<div class="thumb"><img src="/assets/img/{name}-sm.webp" width="720" height="540" '
            f'alt="{esc(PHOTO_ALT[name])}" loading="lazy" decoding="async"></div>')


SINGULAR = {"services": "Service", "industries": "Industry", "work": "Case study", "writing": "Article"}


def related_card(p):
    k = SINGULAR[p["section"]]
    stat = f'<div class="stat">{esc(p["stat"])}</div>' if p.get("stat") else ""
    return (f'<li class="card">{thumb(p)}<span class="card-k">{esc(k)}</span>{stat}'
            f'<h3><a href="{p["url"]}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p>'
            f'<span class="more">Read it</span></li>')


def related_block(pages, refs):
    cards = [related_card(p) for p in refs if p]
    if not cards:
        return ""
    return f'<div class="related"><h2>Related</h2><ul class="cards">{"".join(cards)}</ul></div>'


# ---------------------------------------------------------------- page types
def page_head(eyebrow, h1, lede, trail, extra="", cls="", after=""):
    lede_html = f'<p class="page-lede">{lede}</p>' if lede else ""
    text = f"""{crumbs(trail)}
    <span class="eyebrow">{esc(eyebrow)}</span>
    <h1>{h1}</h1>
    {lede_html}{extra}"""
    classes = " ".join(c for c in ["page-head", cls] if c)
    return f"""<section class="{classes}">
  <div class="container">
    {text}{after}
  </div>
</section>"""


def build_service(p, pages):
    trail = [("Services", "/services/"), (p["title"], p["url"])]
    head = page_head("Service", esc(p["title"]), esc(p["lede"]), trail,
                     extra=f'<div class="meta-row"><b>{esc(p["meta_line"])}</b></div>')
    side = glance(pairs(p.get("glance")), book_btn())
    rel = related_block(pages, [lookup(pages, "work", s) for s in p.get("related", "").split(",") if s.strip()]
                        + [lookup(pages, "writing", s) for s in p.get("reading", "").split(",") if s.strip()])
    body = f"""{head}
<section class="page-body">
  <div class="container split">
    <div class="prose">{p['body']}</div>
    {side}
  </div>
  <div class="container">{rel}</div>
</section>
{closing("Not sure which fits?", "Thirty minutes, free. We will work out whether this is the right shape of engagement, or whether another one is.")}"""
    p["title_tag"] = f"{p['title']}: {p['description_short']} | Millwright Data" if p.get("description_short") else f"{p['title']} | Millwright Data"
    service_ld = {"@type": "Service", "name": p["title"], "description": p["description"], "url": SITE + p["url"],
                  "serviceType": p.get("service_type", p["title"]), "provider": PUBLISHER,
                  "areaServed": ["United States", "European Union"]}
    write(p["url"], render(p, body, "services", [breadcrumb_ld(trail), service_ld]))


def build_industry(p, pages):
    trail = [("Industries", "/industries/"), (p["title"], p["url"])]
    head = page_head("Industry", esc(p["h1"]), esc(p["lede"]), trail)
    side = glance(pairs(p.get("glance")), book_btn())
    rel = related_block(pages, [lookup(pages, "work", s) for s in p.get("related", "").split(",") if s.strip()]
                        + [lookup(pages, "services", s) for s in p.get("services", "").split(",") if s.strip()])
    body = f"""{head}
<section class="page-body">
  <div class="container split">
    <div class="prose">{p['body']}</div>
    {side}
  </div>
  <div class="container">{rel}</div>
</section>
{closing("Working in " + (p["title"] if p["title"][1:] != p["title"][1:].lower() else p["title"].lower()) + "?", "Bring the number that moved or the bill that grew. You will leave the call with a first read and a straight answer on whether I can help.")}"""
    p["title_tag"] = f"{p['h1']} | Millwright Data"
    write(p["url"], render(p, body, "industries", [breadcrumb_ld(trail)]))


def build_work(p, pages):
    trail = [("Case studies", "/work/"), (p["title"], p["url"])]
    stats = "".join(f'<div><span class="n">{esc(k)}</span><span class="l">{esc(v)}</span></div>'
                    for k, v in pairs(p.get("stats")))
    head = page_head(f"Case study · {p['industry']}", esc(p["title"]), esc(p["lede"]), trail,
                     after=f'<div class="stat-band">{stats}</div>')
    side = glance(pairs(p.get("glance")))
    prov = ('<p class="provenance">This work comes from an in-house leadership role, not a Millwright Data client engagement. '
            'The company is not named. The figures are ones I can walk you through on a call.</p>')
    rel = related_block(pages, [lookup(pages, "services", s) for s in p.get("services", "").split(",") if s.strip()]
                        + [lookup(pages, "industries", s) for s in p.get("industry_slug", "").split(",") if s.strip()])
    body = f"""{head}
<section class="page-body">
  <div class="container split">
    <div class="prose">{p['body']}{prov}</div>
    {side}
  </div>
  <div class="container">{rel}</div>
</section>
{closing("Facing something similar?", "Thirty minutes, free. Tell me what is broken and I will tell you whether this is the kind of work I can help with.")}"""
    p["title_tag"] = f"{p['title']} | Case study | Millwright Data"
    art = {"@type": "Article", "headline": p["title"], "description": p["description"], "url": SITE + p["url"],
           "author": AUTHOR, "publisher": PUBLISHER, "image": SITE + "/og-v2.png",
           "datePublished": p.get("date", TODAY), "about": p["industry"]}
    write(p["url"], render(p, body, "work", [breadcrumb_ld(trail), art], og_type="article"))


def build_article(p, pages):
    trail = [("Writing", "/writing/"), (p["title"], p["url"])]
    n = words(p["answer"] + p["body"])
    minutes = max(1, round(n / 230))
    date = datetime.date.fromisoformat(p.get("date", TODAY))
    p["read_minutes"] = minutes
    p["date_label"] = date.strftime("%B %-d, %Y")
    meta = (f'<div class="meta-row"><span>By <b>Sid Srivastava</b></span>'
            f'<span>{p["date_label"]}</span><span>{minutes} min read</span></div>')
    head = page_head("Writing", esc(p["title"]), "", trail, extra=meta, cls="q")
    answer = f'<div class="answer"><span class="k">Short answer</span><p>{p["answer"]}</p></div>'
    author = ('<div class="author"><img src="/assets/sid.jpg" alt="Portrait of Sid Srivastava" width="60" height="60" loading="lazy">'
              '<p><b>Sid Srivastava</b>Founder of Millwright Data. He has run data platforms in semiconductor '
              'manufacturing, digital health, hospitality, and AAA games, on Snowflake, Databricks, and AWS.</p></div>')
    rel = related_block(pages, [lookup(pages, "services", s) for s in p.get("services", "").split(",") if s.strip()]
                        + [lookup(pages, "work", s) for s in p.get("related", "").split(",") if s.strip()])
    body = f"""{head}
<section class="page-body">
  <div class="container">
    <article class="prose">{answer}{p['body']}{author}</article>
    {rel}
  </div>
</section>
{closing("Want a second opinion on yours?", "Thirty minutes, free. Bring the question and the numbers. You will leave with a first read.")}"""
    p["title_tag"] = f"{p['title']} | Millwright Data"
    art = {"@type": "Article", "headline": p["title"], "description": p["description"], "url": SITE + p["url"],
           "author": AUTHOR, "publisher": PUBLISHER, "image": SITE + "/og-v2.png",
           "datePublished": date.isoformat(), "wordCount": n}
    write(p["url"], render(p, body, "writing", [breadcrumb_ld(trail), art], og_type="article"))


# ---------------------------------------------------------------- index pages
def card_for(p):
    if p["section"] == "services":
        icon = thumb(p) or f'<span class="wb-ico" aria-hidden="true">{ICONS.get(p["slug"], "")}</span>'
        return (f'<li class="card">{icon}<span class="card-k">{esc(p["meta_line"])}</span>'
                f'<h3><a href="{p["url"]}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p>'
                f'<span class="more">How it works</span></li>')
    if p["section"] == "work":
        return (f'<li class="card">{thumb(p)}<span class="card-k">{esc(p["industry"])}</span><div class="stat">{esc(p["stat"])}</div>'
                f'<h3><a href="{p["url"]}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p>'
                f'<span class="more">Read the case study</span></li>')
    return (f'<li class="card">{thumb(p)}<h3><a href="{p["url"]}">{esc(p["title"])}</a></h3>'
            f'<p>{esc(p["summary"])}</p><span class="more">Read more</span></li>')


def post_item(p):
    return (f'<li>{thumb(p)}<div><h3><a href="{p["url"]}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p>'
            f'<span class="meta">{p["date_label"]} · {p["read_minutes"]} min read</span></div></li>')


def linkedin_block():
    post = f"https://www.linkedin.com/feed/update/urn:li:activity:{LINKEDIN_POST}/"
    return f"""<div class="linkedin-latest">
      <h2>Latest from LinkedIn</h2>
      <div class="post">
        <iframe class="post-embed" src="https://www.linkedin.com/embed/feed/update/urn:li:activity:{LINKEDIN_POST}" title="Latest LinkedIn post by Sid Srivastava" loading="lazy" allowfullscreen></iframe>
        <p class="post-links"><a href="{post}" target="_blank" rel="noopener">Read it on LinkedIn</a> · <a href="{LINKEDIN}" target="_blank" rel="noopener">Follow for more</a></p>
      </div>
    </div>"""


def build_hub(section, items):
    cfg = SECTIONS[section]
    trail = [(cfg["title"], f"/{section}/")]
    share = (f'<p class="share-line">I share each piece on <a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a> too.</p>'
             if section == "writing" else "")
    head = page_head(cfg["eyebrow"], esc(cfg["h1"]), esc(cfg["lede"]), trail, extra=share)
    listing = (f'<ul class="post-list">{"".join(post_item(p) for p in items)}</ul>{linkedin_block()}' if section == "writing"
               else f'<ul class="cards">{"".join(card_for(p) for p in items)}</ul>')
    body = f"""{head}
<section class="page-body"><div class="container">{listing}</div></section>
{closing("Have a question that isn't here?", "Thirty minutes, free. Bring it to a call, or email sid@millwrightdata.com.")}"""
    meta = {"title_tag": f"{cfg['title']} | Millwright Data", "description": cfg["description"], "url": f"/{section}/"}
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": SITE + p["url"], "name": p["title"]} for i, p in enumerate(items, 1)]}
    write(meta["url"], render(meta, body, section, [breadcrumb_ld(trail), item_list]))


# ---------------------------------------------------------------- home page and machine files
def inject(text, marker, content):
    pattern = re.compile(rf"(<!-- build:{marker} -->).*?(<!-- /build:{marker} -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"index.html: missing build:{marker} markers")
    return pattern.sub(lambda m: m.group(1) + "\n" + content + "\n" + m.group(2), text)


def update_home(pages):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = inject(text, "nav", nav(None))
    text = inject(text, "work", "".join(card_for(p) for p in pages["work"]))
    text = inject(text, "writing", "".join(post_item(p) for p in pages["writing"]))
    text = inject(text, "industries", "".join(
        f'<li><a href="{p["url"]}">{esc(p["title"])}</a></li>' for p in pages["industries"]))
    path.write_text(asset_versions(text), encoding="utf-8")


def write_sitemap(pages):
    urls = ["/", "/privacy.html"] + [f"/{s}/" for s in ORDER] + [p["url"] for s in ORDER for p in pages[s]]
    rows = "".join(f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n", encoding="utf-8")
    return len(urls)


def write_llms(pages):
    def block(section, label):
        lines = [f"## {label}", ""]
        for p in pages[section]:
            lines.append(f"- [{p['title']}]({SITE}{p['url']}): {p['summary']}")
        return "\n".join(lines)
    text = "\n\n".join([
        "# Millwright Data",
        "> Millwright Data is the data platform, governance, and AI advisory practice of Sid Srivastava. "
        "It helps companies that run on data with architecture, governance, cloud cost, and the path from a model to production.",
        "Millwright Data operates as Millwright Data LLC in the United States and Millwright Data OÜ in the European Union. "
        "Sid Srivastava has run data platforms in semiconductor manufacturing, digital health, hospitality, AAA games, "
        "SaaS, and utilities, on Snowflake, Databricks, and AWS.",
        block("services", "Services"),
        block("work", "Case studies"),
        block("writing", "Articles"),
        block("industries", "Industries"),
        "## Contact\n\n"
        f"- [Book a thirty-minute intro call]({CAL})\n"
        "- [Email sid@millwrightdata.com](mailto:sid@millwrightdata.com)\n"
        "- [LinkedIn](https://www.linkedin.com/in/srivastava-sid)",
    ])
    (ROOT / "llms.txt").write_text(text + "\n", encoding="utf-8")


def main():
    pages = load()
    for p in pages["services"]:
        build_service(p, pages)
    for p in pages["industries"]:
        build_industry(p, pages)
    for p in pages["work"]:
        build_work(p, pages)
    for p in pages["writing"]:
        build_article(p, pages)
    for section in ORDER:
        build_hub(section, pages[section])
    update_home(pages)
    n = write_sitemap(pages)
    write_llms(pages)
    counts = ", ".join(f"{len(pages[s])} {s}" for s in ORDER)
    print(f"built {counts}, plus 4 index pages. sitemap: {n} urls")


if __name__ == "__main__":
    main()
