#!/usr/bin/env python3
"""Portugal Life Compass — static site builder.
No external dependencies. Usage: python3 build.py  →  output in ./dist
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://portugallifecompass.com"
YT_CHANNEL = "https://youtube.com/@portugallifecompass"

BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
EPISODES = json.loads((ROOT / "data" / "episodes.json").read_text(encoding="utf-8"))


def render(title, description, path, content, head_extra=""):
    html = (BASE.replace("{{title}}", title)
                .replace("{{description}}", description)
                .replace("{{path}}", path)
                .replace("{{head_extra}}", head_extra)
                .replace("{{content}}", content))
    out = DIST / path.lstrip("/") / "index.html" if path != "/" else DIST / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return path


def ep_card(ep):
    live = ep["status"] == "published"
    badge = ('<span class="ep-badge live">Published</span>' if live
             else f'<span class="ep-badge">Premieres {ep["date_label"]}</span>')
    guide_link = (f'<a class="ep-link" href="/guides/{ep["slug"]}/">Read the guide →</a>'
                  if ep.get("guide") else "")
    return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{ep["label"].upper()}</span>{badge}</div>
      <p class="ep-title">{ep["title"]}</p>
      {guide_link}
      <a class="ep-link ep-link-sub" href="{ep["url"]}" rel="noopener">Watch on YouTube →</a>
    </div>'''


def build_index():
    cards = "\n".join(ep_card(e) for e in EPISODES)
    content = f'''
<section class="hero"><div class="container">
  <p class="hero-kicker">TAXES · VISAS · MONEY · PORTUGAL</p>
  <h1>Portugal, explained with <span class="gold">CFO-grade rigor</span> — in plain English.</h1>
  <p class="hero-sub">Short, calm, carefully verified videos and guides on Portugal's taxes, visas and cost of living — for expats, remote workers, retirees and investors. Every legal claim checked against official sources before it ships.</p>
  <div class="hero-ctas">
    <a class="btn btn-gold" href="{YT_CHANNEL}" rel="noopener">▶ Watch on YouTube</a>
    <a class="btn btn-ghost" href="/checklist/">Get the free 2026 Checklist</a>
  </div>
  <p class="hero-chip">RULES AS OF JULY 2026 · VERIFIED AT THE SOURCE</p>
</div></section>

<section class="section"><div class="container">
  <h2 class="section-h">Episodes</h2>
  <p class="section-sub">A new episode every Thursday. Guides for each episode are being published here through August–September 2026.</p>
  <div class="ep-grid">{cards}</div>
</div></section>

<section class="section section-alt"><div class="container">
  <h2 class="section-h">Why trust this channel?</h2>
  <p class="section-sub">Because we show our work. Three rules govern everything we publish:</p>
  <div class="method-grid">
    <div class="method-card"><h3>Official sources only</h3><p>Every legal and tax statement is verified against the Diário da República (consolidated legislation), the Portal das Finanças, AIMA and EUR-Lex — never against blogs, forums or "probable" references.</p></div>
    <div class="method-card"><h3>Dated rules</h3><p>Portuguese rules change every year. Everything we publish carries its verification date — "Rules as of July 2026" — and gets updated when the law moves.</p></div>
    <div class="method-card"><h3>Not advice — and we say so</h3><p>We give you the verified map, not a personal route. Every video and page tells you plainly when it's time to talk to a qualified professional.</p></div>
  </div>
</div></section>

<section class="section"><div class="container">
  <div class="cta-band">
    <div>
      <h2>The Portugal Tax Relocation Checklist (2026)</h2>
      <p>The steps that protect you from the most expensive expat tax mistakes — free, one page, verified at the source.</p>
    </div>
    <a class="btn btn-gold" href="/checklist/">Download free →</a>
  </div>
</div></section>'''
    return render("Portugal Life Compass — Portugal's Taxes, Visas & Money, Verified",
                  "Short, verified videos and guides on Portugal's taxes, visas and money for expats, remote workers and retirees. Every legal claim checked against official sources.",
                  "/", content)


def guide_card(e):
    if e.get("guide"):
        return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{e["label"].upper()}</span><span class="ep-badge live">Guide available</span></div>
      <p class="ep-title">{e["guide_title"]}</p>
      <a class="ep-link" href="/guides/{e["slug"]}/">Read the guide →</a>
      <a class="ep-link ep-link-sub" href="{e["url"]}" rel="noopener">Watch the episode →</a>
    </div>'''
    return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{e["label"].upper()}</span><span class="ep-badge">Guide coming soon</span></div>
      <p class="ep-title">{e["title"]}</p>
      <a class="ep-link" href="{e["url"]}" rel="noopener">Watch the episode →</a>
    </div>'''


def build_guides():
    items = "\n".join(guide_card(e) for e in EPISODES)
    content = f'''
<div class="page-head"><div class="container">
  <h1>Guides</h1>
  <p class="rules-chip">RULES AS OF JULY 2026</p>
</div></div>
<section class="section"><div class="container">
  <p class="section-sub">Written, source-verified guides for every episode. Every legal statement below is checked against official Portuguese sources — the remaining guides are being published through August–September 2026.</p>
  <div class="ep-grid">{items}</div>
</div></section>'''
    return render("Guides — Portugal Life Compass",
                  "Source-verified written guides on Portugal's taxes, visas and money — companion articles to the Portugal Life Compass episodes.",
                  "/guides/", content)


def build_content_pages():
    paths = []
    for f in sorted((ROOT / "content").glob("**/*.html")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"<!--(.*?)-->", raw, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1).strip(), re.M))
        body = raw[m.end():].strip()
        paths.append(render(meta["title"], meta["description"], meta["path"], body))
    return paths


def build_extras(paths):
    urls = "\n".join(f"  <url><loc>{SITE}{p}</loc></url>" for p in paths)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n",
        encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "static" / "css", DIST / "css")
    shutil.copytree(ROOT / "static" / "img", DIST / "img")
    paths = [build_index(), build_guides()] + build_content_pages()
    build_extras(paths)
    print(f"Built {len(paths)} pages → {DIST}")
    for p in sorted(paths):
        print("  ", p)


if __name__ == "__main__":
    main()
