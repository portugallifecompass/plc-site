#!/usr/bin/env python3
"""Portugal Life Compass — static site builder.
No external dependencies. Usage: python3 build.py  →  output in ./dist
"""
import html as _html
import json, re, shutil
from datetime import date as _date, datetime as _datetime
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://portugallifecompass.com"
YT_CHANNEL = "https://youtube.com/@portugallifecompass"
OG_IMAGE = "/img/og-default.png"   # 1200x630, gerado a 27/08/2026
BUILD_DATE = _date.today()
HORA_ESTREIA = 17          # todas as estreias sao as 17:00 hora de Portugal

BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
EPISODES = json.loads((ROOT / "data" / "episodes.json").read_text(encoding="utf-8"))

# --------------------------------------------------------------------------
# 30/08/2026 - DURACOES lidas no YouTube Studio, video a video, e nao estimadas.
# Servem o "duration" do VideoObject, que faltava nos onze guias (defeito 9 da
# revisao de 27/08). Formato ISO 8601, exigido pelo schema.org.
# --------------------------------------------------------------------------
DURACOES = {
    "QZQkfqIjAYM": "PT5M23S",  # Ep12 — acrescentado 01/09/2026
    "sKj7SaRgl6o": "PT4M8S",   "ECnct105JV0": "PT4M28S", "ttFby22DOFE": "PT3M17S",
    "j0G6ShPWd44": "PT2M51S",  "1R3qsRKGIkg": "PT3M17S", "oKxJHpxJSQg": "PT3M20S",
    "9CXVyx99F1E": "PT3M11S",  "JvW3NlYoH_k": "PT3M21S", "Ghx8KynGTbA": "PT3M26S",
    "TOGdqwQ3TPY": "PT3M33S",  "j6RRm1KF2_E": "PT3M21S",
}

# --------------------------------------------------------------------------
# 30/08/2026 - LIGACAO INTERNA GUIA-A-GUIA (defeito 8 da revisao de 27/08).
# Medido nessa revisao: nove guias tinham UMA ligacao a outro guia, um tinha
# DUAS e o do D7 tinha ZERO - era um beco. O bloco e' gerado aqui, e nao
# escrito em cada ficheiro, para que o grafo se possa ler e conferir num
# sitio so. Conferido: nenhum guia fica sem ligacoes de entrada.
# --------------------------------------------------------------------------
RELACIONADOS = {
    "portugal-healthcare-sns-private-insurance": ["d7-visa-income-requirements", "portugal-self-employed-social-security", "portugal-tax-mistakes"],
    "portugal-tax-mistakes":                ["nif-fiscal-representative-portugal", "portugal-double-taxation-treaties", "portugal-crypto-taxes"],
    "ifici-portugal-20-percent-tax":        ["portugal-tax-mistakes", "d7-visa-income-requirements", "portugal-self-employed-social-security"],
    "d7-visa-income-requirements":          ["ifici-portugal-20-percent-tax", "portugal-foreign-pension-tax", "portugal-golden-visa-remote-work"],
    "portugal-foreign-pension-tax":         ["portugal-double-taxation-treaties", "d7-visa-income-requirements", "ifici-portugal-20-percent-tax"],
    "portugal-double-taxation-treaties":    ["portugal-foreign-pension-tax", "portugal-tax-mistakes", "nif-fiscal-representative-portugal"],
    "nif-fiscal-representative-portugal":   ["portugal-tax-mistakes", "portugal-property-purchase-taxes", "d7-visa-income-requirements"],
    "portugal-property-purchase-taxes":     ["portugal-property-capital-gains", "nif-fiscal-representative-portugal", "portugal-tax-mistakes"],
    "portugal-property-capital-gains":      ["portugal-property-purchase-taxes", "portugal-crypto-taxes", "portugal-double-taxation-treaties"],
    "portugal-self-employed-social-security":["d7-visa-income-requirements", "ifici-portugal-20-percent-tax", "portugal-tax-mistakes"],
    "portugal-crypto-taxes":                ["portugal-tax-mistakes", "portugal-property-capital-gains", "portugal-golden-visa-remote-work"],
    "portugal-golden-visa-remote-work":     ["d7-visa-income-requirements", "portugal-self-employed-social-security", "ifici-portugal-20-percent-tax"],
}

EP_POR_SLUG = {e["slug"]: e for e in EPISODES}
EP_POR_PATH = {"/guides/%s/" % e["slug"]: e for e in EPISODES}


def _vid(ep):
    """O id do video a partir do url curto youtu.be/<id>."""
    return ep["url"].rstrip("/").rsplit("/", 1)[-1]


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

# ------------------------------------------------------------------
# 5 · APANHA-TUDO DO /go/ — 01/09/2026, decisao do utilizador.
#
#     Medido em producao a 01/09: /go/nope devolvia 200 com uma pagina,
#     enquanto /isto-nao-existe-de-todo/ ja devolvia 404 a serio. O /go/
#     era a unica familia de caminhos onde uma ligacao mal escrita
#     PARECIA funcionar - que e' exactamente o que a regra 1 no topo
#     deste ficheiro diz ser pior do que um 404.
#
#     Esta linha tem de ficar SEMPRE EM ULTIMO no ficheiro: o Cloudflare
#     Pages avalia por ordem e a primeira regra que casa vence. Cada
#     linha de parceiro real entra ACIMA desta, nunca abaixo, senao
#     nunca chega a ser avaliada.
# ------------------------------------------------------------------
/go/*    /404.html    404
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


def _hora_portugal():
    """30/08/2026 - a regra de 28/08 usava _datetime.now().hour, ou seja a hora
    LOCAL da maquina que constroi. Isso e' correcto no Windows do dono, que
    corre em hora de Portugal, e ERRADO em qualquer maquina em UTC - onde as
    17:30 de Lisboa sao as 16:30 e o cartao continuaria a dizer "Premieres".
    Nao e' hipotese: o ambiente Linux ligado a esta pasta corre em UTC.

    Tenta-se a zona horaria explicita e cai-se na hora local se a base de
    fusos nao existir - que foi a razao pela qual a versao de 28/08 nao a
    usou. O comportamento no Windows do dono nao muda.
    """
    try:
        from zoneinfo import ZoneInfo
        return _datetime.now(ZoneInfo("Europe/Lisbon")).hour
    except Exception:
        return _datetime.now().hour


def is_live(ep):
    """CORRECCAO 27/08/2026 - o estado passa a ser DERIVADO da data de estreia.

    Antes vinha do campo "status" de data/episodes.json, escrito a mao. Ficou
    congelado em Julho: o Ep3 (31/07), o Ep4 (07/08), o Ep5 (14/08) e o Ep6
    (21/08) estavam ha semanas no ar e a pagina inicial continuava a anunciar
    "Premieres". Um campo que so muda quando alguem se lembra de o mudar nao e
    um estado - e uma promessa de manutencao que ninguem cumpre.

    CORRECCAO 28/08/2026 - a regra anterior comparava so DATAS, estritamente
    anterior ao dia do build. O comentario dizia que "o build que se corre no
    dia da estreia faz o cartao passar a Published", e isso era falso: com
    data < hoje, um build corrido a 28/08 as 18:00 continuava a anunciar
    "Premieres 28 August" com o video ja publico desde as 17:00. O defeito
    apareceu no proprio dia do Ep7.

    A regra passa a ter HORA. Um episodio esta no ar se a data ja passou, ou
    se e hoje e ja sao 17:00 ou mais - que e a hora a que todas as estreias
    estao marcadas. Usa-se a hora local da maquina que constroi (Portugal),
    sem depender de base de fusos horarios, que no Windows pode nao existir.

    O campo "status" fica no JSON e serve so de recurso se a data nao ler.
    """
    try:
        d = _date.fromisoformat(ep["date"])
        if d < BUILD_DATE:
            return True
        if d == BUILD_DATE:
            return _hora_portugal() >= HORA_ESTREIA
        return False
    except Exception:
        return ep.get("status") == "published"


def atributos_estreia(ep):
    """01/09/2026 - a palavra Published deixa de depender do build.

    Ate hoje, o estado de um episodio era calculado no momento do build. Como
    o Cloudflare Pages serve o dist/ verbatim e nao corre build nenhum, isso
    obrigava a um DEPLOY MANUAL no dia de cada estreia - quatro deles estavam
    inscritos no cronograma para 04/09, 11/09, 18/09 e 25/09.

    Passa a ser calculado no browser de quem visita, contra a hora da estreia
    escrita aqui em ISO com o fuso de Lisboa. O HTML continua a sair com o
    estado correcto A' DATA DO BUILD, pelo que uma pagina sem JavaScript
    continua certa ate a' estreia e so deixa de o ser depois dela - nunca
    antes, que e' o erro que importa evitar (prometer publico o que e' privado).
    """
    d = ep["date"]
    # Julho a Outubro em Portugal continental: UTC+01:00. Novembro a Marco: Z.
    fuso = "+01:00" if "-04-" <= d[4:8] <= "-10-" else "+00:00"
    return ('data-live-at="%sT17:00:00%s" data-yt="%s" data-yt-channel="%s" '
            'data-date-label="%s"' % (d, fuso, ep["url"], YT_CHANNEL, ep["date_label"]))


def ep_card(ep):
    live = is_live(ep)
    badge = ('<span class="ep-badge live">Published</span>' if live
             else f'<span class="ep-badge">Premieres {ep["date_label"]}</span>')
    guide_link = (f'<a class="ep-link" href="/guides/{ep["slug"]}/">Read the guide →</a>'
                  if ep.get("guide") else "")
    return f'''<div class="ep-card" {atributos_estreia(ep)}>
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
    # 30/08/2026 - defeito 10 da revisao de 27/08: as seis paginas nao-guia
    # nao tinham dados estruturados nenhuns. A home leva Organization e WebSite.
    ld = json_ld([
        {"@context": "https://schema.org", "@type": "Organization",
         "name": "Portugal Life Compass", "url": SITE + "/",
         "logo": SITE + "/img/logo.svg",
         "description": "Source-verified explanations of Portugal's taxes, visas and money for expats, remote workers, retirees and investors.",
         "sameAs": [YT_CHANNEL]},
        {"@context": "https://schema.org", "@type": "WebSite",
         "name": "Portugal Life Compass", "url": SITE + "/",
         "inLanguage": "en", "publisher": {"@type": "Organization", "name": "Portugal Life Compass"}},
    ])
    return render("Portugal Life Compass — Portugal's Taxes, Visas & Money, Verified",
                  "Short, verified videos and guides on Portugal's taxes, visas and money for expats, remote workers and retirees. Every legal claim checked against official sources.",
                  "/", content, ld)


def guide_card(e):
    # 27/08/2026 - a mesma regra do ep_card: um episodio que ainda nao estreou
    # nao recebe ligacao ao video, porque o video e' privado e o clique morre em
    # "video indisponivel". O indice dos guias tinha ficado de fora da primeira
    # passagem desta correccao, e foi a medicao em producao que o mostrou.
    live = is_live(e)
    destino = e["url"] if live else YT_CHANNEL
    rotulo = "Watch the episode →" if live else "Go to the channel →"
    if e.get("guide"):
        return f'''<div class="ep-card" {atributos_estreia(e)}>
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
    # 30/08/2026 - ItemList com os guias que existem, pela ordem em que sao
    # listados. So entram os que tem guia: anunciar um item que devolve 404
    # e' pior do que nao ter ItemList.
    com_guia = [e for e in EPISODES if e.get("guide")]
    ld = json_ld({"@context": "https://schema.org", "@type": "ItemList",
                  "name": "Portugal Life Compass guides",
                  "numberOfItems": len(com_guia),
                  "itemListElement": [
                      {"@type": "ListItem", "position": i + 1, "name": e["guide_title"],
                       "url": "%s/guides/%s/" % (SITE, e["slug"])}
                      for i, e in enumerate(com_guia)]})
    return render("Guides — Portugal Life Compass",
                  "Source-verified written guides on Portugal's taxes, visas and money — companion articles to the Portugal Life Compass episodes.",
                  "/guides/", content, ld)


def cartao_watch(ep):
    """30/08/2026 - a linha wc-sub do guia passa a ser DERIVADA, como ja eram
    o ep_card e o guide_card desde 27/08.

    Antes estava escrita a mao em cada ficheiro de conteudo, e por isso tinha
    os dois defeitos da classe: QUATRO guias anunciavam "Premieres <data>" com
    a data ja passada (D7 31/07, pensoes 07/08, dupla tributacao 14/08, NIF
    21/08), e a reversao da ligacao ao video no dia da estreia era um acto
    manual inscrito no cronograma - 04/09, 11/09, 18/09 e 25/09 - com o
    endereco do video copiado a mao em cada um.

    Passa a bastar correr o build. O endereco vem do episodes.json e nao de
    uma colagem, e a palavra segue a mesma regra de hora da is_live().
    """
    live = is_live(ep)
    destino = ep["url"] if live else YT_CHANNEL
    rotulo = "Watch on YouTube" if live else "Go to the channel"
    estado = ("Published " if live else "Premieres ") + ep["date_label"]
    return ('<p class="wc-sub" %s><a href="%s" rel="noopener">%s</a> \u00b7 %s</p>'
            % (atributos_estreia(ep), destino, rotulo, estado))


def bloco_relacionados(slug):
    alvos = RELACIONADOS.get(slug, [])
    if not alvos:
        return ""
    itens = "".join(
        '<li><a href="/guides/%s/">%s</a></li>' % (s, EP_POR_SLUG[s]["guide_title"])
        for s in alvos if s in EP_POR_SLUG)
    return ('\n  <h2>Related guides</h2>\n  <nav class="related-guides" aria-label="Related guides">'
            '<ul>%s</ul></nav>\n' % itens)


def json_ld(obj):
    return ('<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def breadcrumb(ep):
    return json_ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
        {"@type": "ListItem", "position": 3, "name": ep["guide_title"], "item": "%s/guides/%s/" % (SITE, ep["slug"])},
    ]})


def completar_videoobject(body, ep):
    """30/08/2026 - defeito 9 da revisao de 27/08: os onze VideoObject tinham
    name, contentUrl, uploadDate e thumbnailUrl, e nao tinham duration nem
    embedUrl. Acrescentam-se aqui, DERIVADOS - a duracao vem da tabela lida
    no Studio, o embedUrl do proprio id. Se a duracao nao estiver na tabela,
    nao se inventa: acrescenta-se so o embedUrl."""
    vid = _vid(ep)
    extra = '"embedUrl":"https://www.youtube.com/embed/%s"' % vid
    dur = DURACOES.get(vid)
    if dur:
        extra = '"duration":"%s",' % dur + extra
    alvo = '"contentUrl":"%s"' % ep["url"]
    assert alvo in body, "contentUrl nao encontrado no VideoObject de %s" % ep["slug"]
    body = body.replace(alvo, alvo + "," + extra, 1)

    # 30/08/2026 - o bloco "publication"/BroadcastEvent com isLiveBroadcast:true
    # anuncia uma estreia FUTURA. Depois de a estreia passar fica a declarar,
    # em dados estruturados, que um video de ha semanas esta em directo. Quatro
    # guias estavam nesse estado (piloto e Ep2 nao tinham o bloco; o Ep7 tinha-o
    # com data de 28/08). Retira-se assim que o episodio esta no ar, pela mesma
    # regra de data e hora da is_live() - nao ha campo para manter a mao.
    if is_live(ep):
        body = re.sub(r',"publication":\{[^{}]*\}', "", body, count=1)
    return body


def build_content_pages():
    paths = []
    for f in sorted((ROOT / "content").glob("**/*.html")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"<!--(.*?)-->", raw, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1).strip(), re.M))
        body = raw[m.end():].strip()
        extra = ""
        ep = EP_POR_PATH.get(meta["path"])
        if ep:
            novo = cartao_watch(ep)
            body, k = re.subn(r'<p class="wc-sub">.*?</p>', lambda _m: novo, body, count=1, flags=re.S)
            assert k == 1, "wc-sub nao encontrada em %s" % f.name
            body = completar_videoobject(body, ep)
            rel = bloco_relacionados(ep["slug"])
            assert "<h2>Sources</h2>" in body, "ancora Sources ausente em %s" % f.name
            body = body.replace("<h2>Sources</h2>", rel + "\n  <h2>Sources</h2>", 1)
            extra = breadcrumb(ep)
        else:
            # 30/08/2026 - as paginas estaticas (/about/, /checklist/,
            # /disclaimer/, /privacy/) tambem nao tinham dados estruturados.
            # WebPage + BreadcrumbList de dois niveis, que e' o que sao.
            extra = json_ld([
                {"@context": "https://schema.org", "@type": "WebPage",
                 "name": meta["title"], "description": meta["description"],
                 "url": SITE + meta["path"], "inLanguage": "en",
                 "isPartOf": {"@type": "WebSite", "name": "Portugal Life Compass", "url": SITE + "/"},
                 "publisher": {"@type": "Organization", "name": "Portugal Life Compass"}},
                {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": meta["title"].split(" \u2014 ")[0], "item": SITE + meta["path"]}]},
            ])
        paths.append(render(meta["title"], meta["description"], meta["path"], body, extra))
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
