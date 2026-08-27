#!/usr/bin/env python3
"""Portugal Life Compass — static site builder.
No external dependencies. Usage: python3 build.py  →  output in ./dist
"""
import html as _html
import json, re, shutil
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://portugallifecompass.com"
YT_CHANNEL = "https://youtube.com/@portugallifecompass"
OG_IMAGE = "/img/og-default.png"   # 1200x630, gerado a 27/08/2026
BUILD_DATE = _date.today()

BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
EPISODES = json.loads((ROOT / "data" / "episodes.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# _redirects — Cloudflare Pages
# Origem da especificacao: claude/PLC-0708-A4_Afiliados_IMG_e_Redirects_2026-08-07.md
# Correcao do mecanismo:   claude/PLC-1008-I1_... (13/08/2026)
#
# POR QUE VIVE AQUI, E NAO EM dist/ NEM EM static/:
#   main() faz shutil.rmtree(DIST) a cada execucao -> um ficheiro colado a
#   mao em dist/ desaparece no build seguinte.
#   main() so copia static/css, static/img e static/downloads -> um ficheiro
#   colado em static/ nunca chega a dist/.
#   O _headers sobrevive porque e GERADO aqui. O _redirects passa a sobreviver
#   pela mesma razao, e nao por outra.
# --------------------------------------------------------------------------
REDIRECTS = """# _redirects — Cloudflare Pages
# Portugal Life Compass · portugallifecompass.com
# GERADO POR build.py — nao editar em dist/. Editar aqui, em build.py.
#
# REGRA 1 — Nenhuma linha de parceiro sai de comentario sem um URL de
#           rastreio REAL, emitido pela plataforma apos a aprovacao.
#           Um /go/ que aponta para um destino inventado e pior do que
#           um 404: parece funcionar.
#
# REGRA 2 — A linha de um parceiro e a sua divulgacao publicam-se no
#           MESMO commit: /disclosure no ar e a seccao do /disclaimer
#           corrigida, porque a pagina publicada declara hoje que o site
#           nao tem links de afiliado.
#
# REGRA 3 — 302 sempre, nunca 301. Os URLs de rastreio mudam; um 301
#           fica em cache no browser do visitante e nao se desfaz.
#
# REGRA 4 — Cada origem leva SEMPRE duas linhas: sem barra final e com
#           barra final. O Cloudflare Pages nao as trata como iguais.
#
# Sintaxe: [origem] [destino] [codigo]
# Linhas iniciadas por # sao comentarios.

# ------------------------------------------------------------------
# 1 · SONDA DE MECANISMO — REMOVIDA a 13/08/2026, cumprida a funcao.
#     Medido em producao nesse dia, com curl.exe na maquina do dono:
#       /go/test          -> 302 https://portugallifecompass.com/disclaimer/
#       /go/test/         -> 302 https://portugallifecompass.com/disclaimer/
#       /go/test?src=ep12 -> 302 .../disclaimer/?src=ep12  (QUERY STRING PASSA)
#       /go/TEST          -> 200, sem redirecionamento (SENSIVEL A MAIUSCULAS)
#     O mecanismo esta provado. Registo: PLC-1008-I1 (13/08/2026).
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# 2 · VAGA 1 (25-31/08/2026) — SafetyWing, Genki
# ------------------------------------------------------------------
# /go/safetywing    COLAR_URL_RASTREIO_SAFETYWING    302
# /go/safetywing/   COLAR_URL_RASTREIO_SAFETYWING    302
# /go/genki         COLAR_URL_RASTREIO_GENKI         302
# /go/genki/        COLAR_URL_RASTREIO_GENKI         302

# ------------------------------------------------------------------
# 3 · VAGA 5 (apos o guia de saude estar no ar) — IMG, Cigna
#     ATENCAO IMG: qualquer peca publicada que nomeie a IMG carece de
#     disclaimer e de aprovacao previa da IMG.
# ------------------------------------------------------------------
# /go/img           COLAR_URL_RASTREIO_IMG_IMPACT    302
# /go/img/          COLAR_URL_RASTREIO_IMG_IMPACT    302
# /go/cigna         COLAR_URL_RASTREIO_CIGNA_FLEX    302
# /go/cigna/        COLAR_URL_RASTREIO_CIGNA_FLEX    302

# ------------------------------------------------------------------
# 4 · SLUGS RESERVADOS — shortlist v2, vagas 2 a 6. NAO criar agora.
#     wise · revolut · e-residence · anchorless · practice-portuguese
#     italki · preply · flatio · spotahome · nordvpn
#     Variantes por colocacao, so quando a rede confirmar sub-ID:
#     /go/<parceiro>-yt · -guide · -short · -mail
# ------------------------------------------------------------------
"""


def render(title, description, path, content, head_extra=""):
    # CORRECCAO 27/08/2026 - title e description sao interpolados DENTRO de
    # atributos HTML (content="..."). Sem escape, uma aspa recta no texto fecha
    # o atributo e o resto da frase vira atributos invalidos. Aconteceu em
    # producao em DUAS paginas: a description de portugal-property-capital-gains
    # renderizava literalmente "The " (4 caracteres) porque a copy diz
    # 'The "flat 28% for foreigners" is a myth'. Escapar aqui corrige a CLASSE
    # do defeito e nao as duas ocorrencias - a copy mantem as aspas.
    e = lambda x: _html.escape(x, quote=True)
    html = (BASE.replace("{{title}}", e(title))
                .replace("{{description}}", e(description))
                .replace("{{yt_channel}}", YT_CHANNEL)
                .replace("{{og_image}}", SITE + OG_IMAGE)
                .replace("{{path}}", path)
                .replace("{{head_extra}}", head_extra)
                .replace("{{content}}", content))
    out = DIST / path.lstrip("/") / "index.html" if path != "/" else DIST / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return path


def is_live(ep):
    """CORRECCAO 27/08/2026 - o estado passa a ser DERIVADO da data de estreia.

    Antes vinha do campo "status" de data/episodes.json, escrito a mao. Ficou
    congelado em Julho: o Ep3 (31/07), o Ep4 (07/08), o Ep5 (14/08) e o Ep6
    (21/08) estavam ha semanas no ar e a pagina inicial continuava a anunciar
    "Premieres". Um campo que so muda quando alguem se lembra de o mudar nao e
    um estado - e uma promessa de manutencao que ninguem cumpre.

    Estritamente ANTERIOR ao dia do build: no proprio dia da estreia o cartao
    continua a dizer "Premieres <hoje>", que e verdade ate as 17:00. O build
    que se corre nesse dia (ja inscrito no cronograma, a par da reversao da
    ligacao do guia) faz o cartao passar a Published.

    O campo "status" fica no JSON e serve so de recurso se a data nao ler.
    """
    try:
        return _date.fromisoformat(ep["date"]) < BUILD_DATE
    except Exception:
        return ep.get("status") == "published"


def ep_card(ep):
    live = is_live(ep)
    badge = ('<span class="ep-badge live">Published</span>' if live
             else f'<span class="ep-badge">Premieres {ep["date_label"]}</span>')
    guide_link = (f'<a class="ep-link" href="/guides/{ep["slug"]}/">Read the guide →</a>'
                  if ep.get("guide") else "")
    return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{ep["label"].upper()}</span>{badge}</div>
      <p class="ep-title">{ep["title"]}</p>
      {guide_link}
      <a class="ep-link ep-link-sub" href="{ep["url"] if live else YT_CHANNEL}" rel="noopener">{"Watch on YouTube →" if live else "Go to the channel →"}</a>
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
    # 27/08/2026 - a mesma regra do ep_card: um episodio que ainda nao estreou
    # nao recebe ligacao ao video, porque o video e' privado e o clique morre em
    # "video indisponivel". O indice dos guias tinha ficado de fora da primeira
    # passagem desta correccao, e foi a medicao em producao que o mostrou.
    live = is_live(e)
    destino = e["url"] if live else YT_CHANNEL
    rotulo = "Watch the episode →" if live else "Go to the channel →"
    if e.get("guide"):
        return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{e["label"].upper()}</span><span class="ep-badge live">Guide available</span></div>
      <p class="ep-title">{e["guide_title"]}</p>
      <a class="ep-link" href="/guides/{e["slug"]}/">Read the guide →</a>
      <a class="ep-link ep-link-sub" href="{destino}" rel="noopener">{rotulo}</a>
    </div>'''
    return f'''<div class="ep-card">
      <div class="ep-meta"><span class="ep-num">{e["label"].upper()}</span><span class="ep-badge">Guide coming soon</span></div>
      <p class="ep-title">{e["title"]}</p>
      <a class="ep-link" href="{destino}" rel="noopener">{rotulo}</a>
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
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /go/\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n",
        encoding="utf-8")
    (DIST / "_redirects").write_text(REDIRECTS, encoding="utf-8")

    # ------------------------------------------------------------------
    # 404.html — ACRESCENTADO 27/08/2026
    # Medido em producao nesse dia: qualquer caminho inexistente devolvia
    # HTTP 200 com o conteudo da PAGINA INICIAL (/blog/, /go/<slug nao
    # configurado>, /isto-nao-existe/). Sao soft 404 em todo o dominio, e o
    # custo e de indexacao: cada URL inexistente e lido como duplicado da
    # home. O Cloudflare Pages serve dist/404.html com status 404 quando o
    # ficheiro existe — e so por isso.
    # ------------------------------------------------------------------
    body404 = '''<section class="page-head"><div class="container">
  <h1>Page not found</h1>
  <p class="lede">That address does not exist on this site. It may have been a typo, an old link, or a page that never existed.</p>
</div></section>
<section class="section"><div class="container">
  <p>Try one of these instead:</p>
  <ul>
    <li><a href="/guides/">All guides</a> — the written companions to every episode, verified at the source.</li>
    <li><a href="/checklist/">The 2026 Checklist</a> — the free relocation checklist.</li>
    <li><a href="/about/">About</a> — who this is for and how we verify.</li>
  </ul>
</div></section>'''
    html404 = (BASE.replace("{{title}}", "Page not found — Portugal Life Compass")
                   .replace("{{description}}", "That page does not exist. Browse the source-verified guides on Portugal's taxes, visas and money.")
                   .replace("{{yt_channel}}", YT_CHANNEL)
                   .replace("{{og_image}}", SITE + OG_IMAGE)
                   .replace("{{path}}", "/404.html")
                   .replace("{{head_extra}}", '<meta name="robots" content="noindex">')
                   .replace("{{content}}", body404))
    (DIST / "404.html").write_text(html404, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "static" / "css", DIST / "css")
    shutil.copytree(ROOT / "static" / "img", DIST / "img")
    if (ROOT / "static" / "downloads").exists():
        shutil.copytree(ROOT / "static" / "downloads", DIST / "downloads")
    paths = [build_index(), build_guides()] + build_content_pages()
    build_extras(paths)
    print(f"Built {len(paths)} pages → {DIST}")
    for p in sorted(paths):
        print("  ", p)


if __name__ == "__main__":
    main()
