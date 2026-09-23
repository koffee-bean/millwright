"""Tell search engines which pages changed, using IndexNow (Bing, Yandex, Seznam,
Naver, and others share submissions).

Runs from .github/workflows/indexnow.yml after every push to main. It works out
which published pages the last commit changed, waits for GitHub Pages to finish
deploying that commit, then submits those URLs. Standard library only.

Run by hand:
  python3 _src/indexnow.py            # pages changed in the last commit
  python3 _src/indexnow.py --all      # every URL in sitemap.xml
  python3 _src/indexnow.py --dry-run  # print what would be sent
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://millwrightdata.com"
HOST = "millwrightdata.com"
KEY = "8b9bdfe224d722798d99dc9c073b68f6"  # also the name and content of /<KEY>.txt
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>(.*?)</loc>", text)


def changed_urls(known):
    """Map files changed in HEAD to their public URLs, keeping only sitemap pages."""
    try:
        out = subprocess.run(["git", "diff", "--name-only", "--diff-filter=d", "HEAD~1", "HEAD"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return []
    urls = []
    for name in out.split():
        if name == "index.html":
            url = SITE + "/"
        elif name.endswith("/index.html"):
            url = f"{SITE}/{name[:-len('index.html')]}"
        elif name.endswith(".html"):
            url = f"{SITE}/{name}"
        else:
            continue
        if url in known and content_changed(name):
            urls.append(url)
    return urls


def content_changed(name):
    """False when the only edits are stylesheet version stamps (?v=...), which change
    on every page whenever site.css or site.js does."""
    diff = subprocess.run(["git", "diff", "-U0", "HEAD~1", "HEAD", "--", name],
                          cwd=ROOT, capture_output=True, text=True).stdout
    removed, added = [], []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line[:1] in "+-":
            (added if line[0] == "+" else removed).append(re.sub(r"\?v=\w+", "", line[1:]))
    return removed != added


def wait_for_pages(sha, timeout=600):
    """Poll the GitHub Pages API until this commit is built, so crawlers see the new page."""
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not (token and repo and sha):
        return
    api = f"https://api.github.com/repos/{repo}/pages/builds/latest"
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(api, headers={"Authorization": f"Bearer {token}",
                                                   "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                build = json.load(r)
            if build.get("commit") == sha and build.get("status") == "built":
                print("GitHub Pages has deployed", sha[:7])
                return
            print("waiting for GitHub Pages:", build.get("status"), (build.get("commit") or "")[:7])
        except Exception as exc:  # a transient API error should not stop the submission
            print("could not read Pages status:", exc)
        time.sleep(20)
    print("gave up waiting for GitHub Pages, submitting anyway")


def submit(urls):
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main(args):
    known = sitemap_urls()
    urls = known if "--all" in args else changed_urls(set(known))
    if not urls:
        print("no page changes to submit")
        return 0
    print(f"{len(urls)} URL(s):", *urls, sep="\n  ")
    if "--dry-run" in args:
        return 0
    wait_for_pages(os.environ.get("GITHUB_SHA"))
    status = submit(urls)
    print("IndexNow responded", status)  # 200 or 202 means accepted
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
