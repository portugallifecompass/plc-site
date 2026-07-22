# plc-site — portugallifecompass.com

Site estático do Portugal Life Compass. Sem dependências externas.

## Estrutura
- `build.py` — gerador (Python 3, biblioteca padrão apenas)
- `templates/base.html` — layout comum (header, footer, SEO)
- `content/*.html` — páginas (front-matter em comentário: title, description, path)
- `data/episodes.json` — lista canónica de episódios (títulos, links, datas)
- `static/` — CSS, logo, favicon
- `dist/` — output do build (é o que o Cloudflare Pages serve)

## Build
```
python3 build.py
```
Gera `dist/` com todas as páginas + sitemap.xml + robots.txt + _headers.

## Publicação (Cloudflare Pages)
- Build command: *(nenhum — o dist/ é commitado)*
- Output directory: `dist`
- Custom domain: portugallifecompass.com

## Regras editoriais (não negociáveis)
1. Toda a afirmação legal deriva dos dossiês de verificação do projeto (fontes oficiais: Diário da República consolidado, Portal das Finanças, AIMA, EUR-Lex). Nada de referências "prováveis".
2. Todas as páginas exibem "Rules as of [mês/ano]" e o disclaimer padrão.
3. Artigos novos: prosa reescrita a partir do guião verificado — nunca transcrições coladas.
4. Após qualquer alteração: correr `python3 build.py`, rever, commit + push (deploy automático).

## Pendências conhecidas (lote A)
- PDF do checklist: link interino para o Google Drive; migrar para ficheiro alojado no site (`/downloads/`) e atualizar `content/checklist.html`.
- Título do episódio piloto em `data/episodes.json` é um rótulo descritivo — reconciliar com o título real do YouTube.
- Artigos dos 12 episódios: lotes B e C.
