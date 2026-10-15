#!/usr/bin/env python3
"""Gera o blog do Camargo Lourenço Advogados a partir dos textos da skill blog-juridico-cla.

Uso:
  python build.py spa   -> dist/blog.html (uma página só, para publicar como artifact no Claude)
  python build.py site  -> dist/site/ (pasta pronta para subir no site: /blog/, um link por texto,
                           sitemap.xml, robots.txt, llms.txt, feed.xml)
Os textos ficam em posts/AAAA-MM-DD-slug.md, no formato do modelo da skill.
"""
import html, json, os, re, sys, unicodedata
from datetime import datetime
import markdown

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(BASE, 'config.json'), encoding='utf-8'))
SITE = CFG['site'].rstrip('/')

AUTORAS = {
    'previdenciario': {'id': 'aline-camargo', 'nome': 'Aline Camargo', 'cargo': 'Advogada Previdenciária',
                       'oab': 'OAB/SP 303.926', 'ini': 'AC', 'area_txt': 'Previdenciário'},
    'trabalhista': {'id': 'lislie-lourenco', 'nome': 'Lislie Lourenço', 'cargo': 'Advogada Trabalhista',
                    'oab': 'OAB/SP 305.834', 'ini': 'LL', 'area_txt': 'Trabalhista'},
    'tributario': {'id': 'aline-camargo', 'nome': 'Aline Camargo', 'cargo': 'Advogada Tributária',
                   'oab': 'OAB/SP 303.926', 'ini': 'AC', 'area_txt': 'Tributário'},
}
AREAS = ['previdenciario', 'trabalhista', 'tributario']
MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro',
         'novembro', 'dezembro']


def esc(s):
    return html.escape(s or '', quote=True)


def plano(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def data_br(d):
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


def ler_post(path):
    txt = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    nome = os.path.basename(path)[:-3]
    m = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', nome)
    slug = m.group(2) if m else nome
    titulo = re.search(r'^# (.+)$', txt, re.M).group(1).strip()
    resumo = (re.search(r'^Resumo para busca[^:]*:\s*(.+)$', txt, re.M) or [None, ''])[1].strip()
    chaves = (re.search(r'^Palavras-chave:\s*(.+)$', txt, re.M) or [None, ''])[1].strip()
    atual = re.search(r'^Atualizado em:\s*(\d{2})/(\d{2})/(\d{4})', txt, re.M)
    data = datetime(int(atual.group(3)), int(atual.group(2)), int(atual.group(1))) if atual else \
        datetime.strptime(m.group(1), '%Y-%m-%d')
    publicado = datetime.strptime(m.group(1), '%Y-%m-%d') if m else data
    # área: linha "Área:" (obrigatória no tributário); sem ela, pela OAB da assinatura
    ma = re.search(r'^Área:\s*(.+)$', txt, re.M)
    if ma:
        area = slugify(ma.group(1)).replace('-', '')
    elif '305.834' in txt and '303.926' not in txt:
        area = 'trabalhista'
    elif '303.926' in txt:
        area = 'previdenciario'
    else:
        raise SystemExit(f'{path}: informe a linha "Área:"')
    if area not in AUTORAS:
        raise SystemExit(f'{path}: área inválida "{area}" (use previdenciario, trabalhista ou tributario)')
    # corpo: depois dos metadados, até a primeira linha "---"
    linhas = txt.split('\n')
    corte = next((i for i, l in enumerate(linhas) if l.strip() == '---'), len(linhas))
    linhas = linhas[:corte]
    ini = max(i for i, l in enumerate(linhas) if re.match(r'^(# |Resumo para busca|Palavras-chave|Atualizado em|Área:)', l)) + 1
    corpo = []
    for l in linhas[ini:]:
        if l.strip() == '---':
            break
        corpo.append(l)
    corpo = '\n'.join(corpo).strip()
    partes = re.split(r'\n(?=## )', corpo, maxsplit=1)
    resposta = partes[0].strip()
    resto = partes[1] if len(partes) > 1 else ''
    # perguntas frequentes
    faq = []
    mf = re.search(r'## Perguntas frequentes\n(.*?)(?=\n## |\Z)', resto, re.S)
    if mf:
        for q, a in re.findall(r'\*\*(.+?\?)\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', mf.group(1), re.S):
            faq.append((q.strip(), re.sub(r'\s+', ' ', a).strip()))
        resto = resto.replace(mf.group(0), '')
    # lista logo depois de um parágrafo precisa de linha em branco para virar lista
    resto = re.sub(r'(?m)^(?!\s*(?:[-*]|\d+\.)\s)(.+)\n(?=\s*(?:[-*]|\d+\.)\s)', r'\1\n\n', resto)
    corpo_html = markdown.markdown(resto, extensions=['extra', 'sane_lists', 'nl2br'])
    corpo_html = re.sub(r'<h2>(.+?)</h2>', lambda x: f'<h2 id="{slugify(plano(x.group(1)))}">{x.group(1)}</h2>', corpo_html)
    # quadro "Na prática do escritório" (observações reais da advogada; só existe se ela escreveu)
    corpo_html = re.sub(r'(<h2 id="na-pratica-do-escritorio">.*?</h2>)(.*?)(?=<h2 |\Z)',
                        lambda x: f'<aside class="pratica">{x.group(1)}<p class="pratica-por">Observação de {AUTORAS[area]["nome"]} a partir dos casos atendidos pelo escritório</p>{x.group(2)}</aside>', corpo_html, flags=re.S)
    resposta_html = markdown.markdown(resposta)
    return dict(slug=slug, titulo=titulo, resumo=resumo, chaves=chaves, data=data, publicado=publicado,
                area=area, resposta_html=resposta_html, resposta=plano(resposta_html), corpo_html=corpo_html,
                faq=faq, texto=plano(resposta_html + corpo_html))


def slugify(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60]


def url_post(p, modo):
    return f'#/{p["slug"]}' if modo == 'spa' else f'/blog/{p["slug"]}/'


def canon(p):
    return f'{SITE}/blog/{p["slug"]}/'


def lista_html(posts, modo):
    out = ['<ul class="cards">']
    for p in posts:
        a = AUTORAS[p['area']]
        busca = esc(' '.join([p['titulo'], p['resumo'], p['chaves'], a['area_txt'], p['texto']]))
        out.append(f'<li data-item data-area="{p["area"]}" data-busca="{busca}"><a class="feat" href="{url_post(p, modo)}">'
                   f'<span class="meta"><span class="tag">{a["area_txt"]}</span>'
                   f'<time datetime="{p["data"]:%Y-%m-%d}">{p["data"]:%d/%m/%Y}</time></span>'
                   f'<h3>{esc(p["titulo"])}</h3><p>{esc(p["resumo"])}</p></a></li>')
    out.append('</ul>')
    return '\n'.join(out)


def lp_do_tema(p):
    """Escolhe a LP ativa mais ligada ao texto (config.json → lps)."""
    texto = slugify(' '.join([p['titulo'], p['chaves'], p['resumo']])).replace('-', ' ')
    melhor, pontos = None, 0
    for lp in CFG.get('lps', []):
        if not lp.get('ativa') or (lp.get('area') and lp['area'] != p['area']):
            continue
        n = sum(1 for t in lp['termos'] if slugify(t).replace('-', ' ') in texto)
        if n > pontos:
            melhor, pontos = lp, n
    return melhor


def post_html(p, posts, modo, visivel):
    a = AUTORAS[p['area']]
    home = '#/' if modo == 'spa' else '/blog/'
    faq = ''
    if p['faq']:
        faq = '<h2 id="perguntas-frequentes">Perguntas frequentes</h2><div class="faq">' + ''.join(
            f'<details><summary>{esc(q)}</summary><p>{esc(r)}</p></details>' for q, r in p['faq']) + '</div>'
    rel = sorted([x for x in posts if x['slug'] != p['slug']], key=lambda x: (x['area'] != p['area'], -x['data'].timestamp()))[:3]
    rel_html = ''
    if rel:
        rel_html = '<aside class="related"><h2>Leia também</h2><ul class="rows">' + ''.join(
            f'<li><a class="row" href="{url_post(x, modo)}"><span class="meta"><span class="tag">{AUTORAS[x["area"]]["area_txt"]}</span>'
            f'<time datetime="{x["data"]:%Y-%m-%d}">{x["data"]:%d/%m/%Y}</time></span><h3>{esc(x["titulo"])}</h3>'
            f'<p>{esc(x["resumo"])}</p></a></li>' for x in rel) + '</ul></aside>'
    wa_svg = ICON['wa']
    lp = lp_do_tema(p)
    lp_html = (f'<p class="lp-link"><a href="{SITE}{lp["caminho"]}">Saiba mais: {esc(lp["nome"])} <span aria-hidden="true">→</span></a></p>'
               if lp else '')
    return f'''<article class="post" data-slug="{p["slug"]}" data-area="{p["area"]}" data-title="{esc(p["titulo"])}" data-resumo="{esc(p["resumo"])}"{'' if visivel else ' hidden'}>
<header class="post-head dark"><div class="wrap">
<a class="back" href="{home}">← Todas as dúvidas</a>
<span class="tag">{a["area_txt"]}</span>
<h1>{esc(p["titulo"])}</h1>
<p class="byline">Por <a href="{url_membro(a["id"], modo)}">{a["nome"]}</a>, {a["cargo"]} · Atualizado em <time datetime="{p["data"]:%Y-%m-%d}">{data_br(p["data"])}</time></p>
</div></header>
<div class="post-body light"><div class="wrap">
<div class="quick"><b>Resposta rápida</b>{p["resposta_html"]}</div>
<div class="prose">{com_faq(p["corpo_html"], faq)}</div>
{lp_html}<p class="note">Este texto é informativo e não substitui a análise de um advogado. Cada caso tem detalhes que podem mudar a resposta.</p>
<a class="author" href="{url_membro(a["id"], modo)}"><div class="mono" aria-hidden="true">{a["ini"]}</div><b>{a["nome"]}</b><span>{a["cargo"]} - Camargo Lourenço Advogados</span></a>
<div class="share"><a class="btn btn-wa" href="#" data-share="wa">{wa_svg} Enviar no WhatsApp</a><button class="btn btn-ghost" data-share="link">Copiar link</button><small class="copied" aria-live="polite"></small></div>
<p class="share"><small>Conhece alguém com essa dúvida? Envie este texto para essa pessoa.</small></p>
{rel_html}
</div></div></article>'''


# ---------- dados estruturados (AEO) ----------
def org():
    return {
        '@type': 'LegalService', '@id': f'{SITE}/#escritorio', 'name': 'Camargo Lourenço Advogados',
        'legalName': 'Camargo & Lourenço Advogados', 'taxID': '40.563.383/0001-20', 'url': SITE,
        'logo': f'{SITE}/blog/assets/logo.png', 'image': f'{SITE}/blog/assets/logo.png',
        'telephone': '+55-11-4382-4240', 'email': 'contato@camargolourenco.adv.br',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Avenida Henriqueta Mendes Guerra, 1330, Sala 305, 3º andar – Inspire Business',
                    'addressLocality': 'Barueri', 'addressRegion': 'SP', 'postalCode': '06401-015', 'addressCountry': 'BR'},
        'areaServed': [{'@type': 'City', 'name': c} for c in CFG['cidades']],
        'knowsAbout': ['Direito Previdenciário', 'INSS', 'Aposentadoria', 'Auxílio-doença', 'BPC/LOAS', 'Pensão por morte',
                       'Auxílio-acidente', 'Direito do Trabalho', 'Rescisão', 'FGTS', 'Horas extras', 'Acidente de trabalho',
                       'Direito Tributário', 'Execução fiscal', 'Defesa do executado', 'Isenção de imposto de renda'],
        'sameAs': ['https://www.instagram.com/camargolourencoadv/', 'https://www.facebook.com/camargolourencoadv',
                   'https://www.tiktok.com/@camargolourencoadv'],
    }


def foto_src(caminho, modo):
    if modo == 'spa':
        import base64
        return 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(BASE, caminho), 'rb').read()).decode()
    return '/blog/' + caminho


def url_membro(id_, modo):
    return '#/equipe' if modo == 'spa' else f'/equipe#{id_}'


def pessoa(area):
    a = AUTORAS[area]
    m = next(x for x in CFG['equipe'] if x['id'] == a['id'])
    return {'@type': 'Person', '@id': f'{SITE}/equipe#{m["id"]}', 'name': m['nome'], 'alternateName': m['nome_completo'],
            'jobTitle': m['cargo'].replace('Sócia · ', ''), 'url': f'{SITE}/equipe#{m["id"]}',
            'worksFor': {'@id': f'{SITE}/#escritorio'}, 'knowsAbout': m['areas'], 'description': ' '.join(m['bio']),
            'alumniOf': [{'@type': 'EducationalOrganization', 'name': f['instituicao']} for f in m['formacao']],
            'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': f['curso'], 'dateCreated': f['ano'],
                               'recognizedBy': {'@type': 'EducationalOrganization', 'name': f['instituicao']}} for f in m['formacao']],
            'email': m.get('email'), 'telephone': '+55-' + re.sub(r'\D', '', m.get('telefone', ''))[:2] + '-' + re.sub(r'\D', '', m.get('telefone', ''))[2:],
            'image': f'{SITE}/blog/{m["foto"]}' if m.get('foto') else None,
            'address': {'@type': 'PostalAddress', 'addressLocality': 'Barueri', 'addressRegion': 'SP', 'addressCountry': 'BR'}}


def equipe_html(modo, visivel):
    blocos = []
    for m in CFG['equipe']:
        foto = (f'<img class="eq-foto" src="{foto_src(m["foto"], modo)}" alt="Foto de {esc(m["nome"])}" width="440" height="528" loading="lazy">' if m.get('foto')
                else f'<div class="eq-foto eq-mono" aria-hidden="true">{m["ini"]}</div>')
        form = ''.join(f'<li>{esc(f["curso"])} — {esc(f["instituicao"])}, {f["ano"]}</li>' for f in m['formacao'])
        bio = ''.join(f'<p>{esc(t)}</p>' for t in m['bio'])
        tel = re.sub(r'\D', '', m.get('telefone', ''))
        contato = ''
        if m.get('email') or tel:
            contato = ('<p class="eq-contato">'
                       + (f'<a href="mailto:{m["email"]}">{m["email"]}</a>' if m.get('email') else '')
                       + (f' · <a href="https://wa.me/55{tel}" target="_blank" rel="noopener">WhatsApp {m["telefone"]}</a>' if tel else '')
                       + '</p>')
        blocos.append(f'''<section class="eq-membro" id="{m["id"]}">{foto}<div class="eq-txt">
<h2>{esc(m["nome_completo"])}</h2><p class="eq-cargo">{esc(m["cargo"])}</p>{bio}
<h3>Formação</h3><ul>{form}</ul>{contato}</div></section>''')
    apres = ''.join(f'<p>{esc(t)}</p>' for t in CFG['escritorio_apresentacao'])
    if CFG.get('escritorio_destaque'):
        apres_dest = f'<p class="eq-destaque">{esc(CFG["escritorio_destaque"])}</p>'
    else:
        apres_dest = ''
    home = '#/' if modo == 'spa' else '/blog/'
    return f'''<article class="post equipe" data-slug="equipe" data-title="Equipe" data-resumo="Conheça as advogadas do Camargo Lourenço Advogados."{'' if visivel else ' hidden'}>
<header class="post-head dark"><div class="wrap"><a class="back" href="{home}">← Todas as dúvidas</a>
<span class="tag">Camargo Lourenço Advogados</span><h1>Equipe</h1><p class="byline">Quem escreve e responde às dúvidas do blog.</p></div></header>
<div class="post-body light"><div class="wrap"><div class="eq-escritorio">{apres}</div>{apres_dest}{"".join(blocos)}</div></div></article>'''


def posting(p):
    return {'@type': 'BlogPosting', '@id': canon(p) + '#artigo', 'headline': p['titulo'], 'description': p['resumo'],
            'abstract': p['resposta'], 'datePublished': f'{p["publicado"]:%Y-%m-%d}', 'dateModified': f'{p["data"]:%Y-%m-%d}',
            'inLanguage': 'pt-BR', 'url': canon(p), 'mainEntityOfPage': canon(p),
            'keywords': p['chaves'], 'articleSection': AUTORAS[p['area']]['area_txt'],
            'author': {'@id': f'{SITE}/equipe#{AUTORAS[p["area"]]["id"]}'}, 'publisher': {'@id': f'{SITE}/#escritorio'},
            'isPartOf': {'@id': f'{SITE}/blog/#blog'}, 'wordCount': len(p['texto'].split()),
            'speakable': {'@type': 'SpeakableSpecification', 'cssSelector': ['.quick']}}


def faqpage(p):
    if not p['faq']:
        return None
    return {'@type': 'FAQPage', '@id': canon(p) + '#faq', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': r}} for q, r in p['faq']]}


def jsonld(grafo):
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': grafo},
                                                              ensure_ascii=False) + '</script>'


def base_grafo(posts):
    return [org(), pessoa('previdenciario'), pessoa('trabalhista'),
            {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE, 'name': 'Camargo Lourenço Advogados',
             'inLanguage': 'pt-BR', 'publisher': {'@id': f'{SITE}/#escritorio'},
             'potentialAction': {'@type': 'SearchAction', 'target': f'{SITE}/blog/?q={{busca}}', 'query-input': 'required name=busca'}},
            {'@type': 'Blog', '@id': f'{SITE}/blog/#blog', 'url': f'{SITE}/blog/', 'name': 'Blog jurídico – Camargo Lourenço Advogados',
             'description': 'Respostas práticas sobre INSS e direitos do trabalhador, em linguagem simples.',
             'inLanguage': 'pt-BR', 'publisher': {'@id': f'{SITE}/#escritorio'},
             'blogPost': [{'@id': canon(p) + '#artigo'} for p in posts]}]


# ---------- rodapé ----------
def svgs():
    f = open(os.path.join(BASE, 'footer_lp.html'), encoding='utf-8').read()
    s = re.findall(r'<svg viewBox="0 0 24 24"[^>]*>.*?</svg>', f, re.S)
    return {'tel': s[0], 'mail': s[1], 'pin': s[2], 'fb': s[3], 'ig': s[4], 'tt': s[5]}


ICON = svgs()
ICON['wa'] = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.8-1.4a.5.5 0 0 0 0-.5l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.3 2.2 2.2 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3z"/></svg>')


def rodape(logo):
    i = ICON
    return f'''<footer class="ft">
  <div class="wrap ft-grid">
    <img class="ft-img" src="{logo}" alt="Camargo Lourenço Advogados" width="685" height="276">
    <div class="ft-mid">
      <div class="ft-row"><span class="ft-it">{i["tel"]}<a href="tel:+551143824240">(11) 4382-4240</a></span>
        <span class="ft-it">{i["wa"]}<a href="https://wa.me/5511963353678" target="_blank" rel="noopener">(11) 96335-3678</a> <span class="ft-area">(previdenciário e tributário)</span></span>
        <span class="ft-it">{i["wa"]}<a href="https://wa.me/5511980347924" target="_blank" rel="noopener">(11) 98034-7924</a> <span class="ft-area">(trabalhista)</span></span></div>
      <div class="ft-row"><span class="ft-it">{i["pin"]}<span class="ft-end">Avenida Henriqueta Mendes Guerra, 1330 - Sala 305 - 3º Andar - Barueri/SP, CEP 06401-015.</span></span></div>
      <p class="ft-copy"><span class="nw">Camargo &amp; Lourenço Advogados ·</span> <span class="nw">OAB/SP 36.265 ·</span> <span class="nw">CNPJ 40.563.383/0001-20</span><br>© {datetime.now().year} Todos os direitos reservados · <a href="https://www.camargolourenco.adv.br/politica-de-privacidade" target="_blank" rel="noopener">Política de Privacidade</a>.</p>
    </div>
    <div class="ft-social">
      <a class="soc fb" href="https://www.facebook.com/camargolourencoadv" target="_blank" rel="noopener" aria-label="Facebook">{i["fb"]}</a>
      <a class="soc ig" href="https://www.instagram.com/camargolourencoadv/" target="_blank" rel="noopener" aria-label="Instagram">{i["ig"]}</a>
      <a class="soc tt" href="https://www.tiktok.com/@camargolourencoadv" target="_blank" rel="noopener" aria-label="TikTok">{i["tt"]}</a>
      <button class="soc wa" id="ft-wa" aria-label="WhatsApp">{i["wa"]}</button>
    </div>
  </div>
</footer>'''


def calc_html(calc_trab_url):
    seta = '<span class="calc-go" aria-hidden="true">→</span>'
    def item_prev(x):
        if not x.get('url'):  # calculadora ainda sem página: aparece como "em breve"
            return f'<li><span class="calc-link off" aria-disabled="true"><span>{esc(x["nome"])}</span><span class="calc-soon">Em breve</span></span></li>'
        return f'<li><a class="calc-link" href="{esc(x["url"])}" target="_blank" rel="noopener"><span>{esc(x["nome"])}</span>{seta}</a></li>'
    prev = ''.join(item_prev(x) for x in CFG['calc_prev'])
    trab = ''.join(f'<li><a class="calc-link" href="{CFG["lp_trabalhista"]}#calc-{x["id"]}" target="_blank" rel="noopener"><span>{esc(x["nome"])}</span>{seta}</a></li>' for x in CFG['calc_trab'])
    return ('<div class="calc-cols">'
            f'<div class="calc-panel prev"><div class="calc-ph"><span class="calc-ic" aria-hidden="true">INSS</span><h3>Previdenciárias</h3></div><ul class="calc-list">{prev}</ul></div>'
            f'<div class="calc-panel trab"><div class="calc-ph"><span class="calc-ic" aria-hidden="true">CLT</span><h3>Trabalhistas</h3></div><ul class="calc-list">{trab}</ul></div>'
            '</div>')


def montar(posts, modo, atual=None, logo=''):
    tpl = open(os.path.join(BASE, 'template.html'), encoding='utf-8').read()
    if modo == 'spa':
        grafo = base_grafo(posts) + [posting(p) for p in posts] + [f for f in map(faqpage, posts) if f]
        posts_html = '\n'.join(post_html(p, posts, modo, False) for p in posts) + equipe_html(modo, False)
        titulo, desc, can, og = 'Blog jurídico | Camargo Lourenço Advogados', CFG['descricao'], f'{SITE}/blog/', 'website'
        lista_oculta = ''
        home, hp, ht, htr = '#/', '#/area/previdenciario', '#/area/trabalhista', '#/area/tributario'
        calc, share = CFG['calc_spa'], json.dumps(CFG.get('artifact_url', ''))
    elif atual is None:
        grafo = base_grafo(posts)
        posts_html, lista_oculta = '', ''
        titulo, desc, can, og = 'Blog jurídico | Camargo Lourenço Advogados', CFG['descricao'], f'{SITE}/blog/', 'website'
        home, hp, ht, htr = '/blog/', '/blog/?area=previdenciario', '/blog/?area=trabalhista', '/blog/?area=tributario'
        calc, share = f'{SITE}/trabalhista#calculadoras', json.dumps(SITE)
    elif atual == 'equipe':
        grafo = base_grafo(posts) + [{'@type': 'AboutPage', '@id': f'{SITE}/equipe', 'url': f'{SITE}/equipe', 'name': 'Equipe — Camargo Lourenço Advogados',
                                      'about': {'@id': f'{SITE}/#escritorio'}, 'mainEntity': [{'@id': f'{SITE}/equipe#{m["id"]}'} for m in CFG['equipe']]}]
        posts_html, lista_oculta = equipe_html(modo, True), 'hidden'
        titulo, desc, can, og = 'Equipe | Camargo Lourenço Advogados', 'Conheça as advogadas do Camargo Lourenço Advogados, em Barueri/SP: formação, especializações e áreas de atuação.', f'{SITE}/equipe', 'profile'
        home, hp, ht, htr = '/blog/', '/blog/?area=previdenciario', '/blog/?area=trabalhista', '/blog/?area=tributario'
        calc, share = f'{SITE}/trabalhista#calculadoras', json.dumps(SITE)
    else:
        p = atual
        grafo = base_grafo(posts) + [posting(p)] + ([faqpage(p)] if p['faq'] else []) + [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': SITE},
                {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': f'{SITE}/blog/'},
                {'@type': 'ListItem', 'position': 3, 'name': p['titulo'], 'item': canon(p)}]}]
        posts_html, lista_oculta = post_html(p, posts, modo, True), 'hidden'
        titulo, desc, can, og = f'{p["titulo"]} | Camargo Lourenço Advogados', p['resumo'], canon(p), 'article'
        home, hp, ht, htr = '/blog/', '/blog/?area=previdenciario', '/blog/?area=trabalhista', '/blog/?area=tributario'
        calc, share = f'{SITE}/trabalhista#calculadoras', json.dumps(SITE)
    rep = {'TITLE': esc(titulo), 'DESCRIPTION': esc(desc), 'CANONICAL': can, 'OGTYPE': og, 'SITE': SITE,
           'JSONLD': jsonld(grafo), 'MODE': modo, 'HOME': home, 'HOME_PREV': hp, 'HOME_TRAB': ht, 'HOME_TRIB': htr, 'HOME_EQUIPE': '#/equipe' if modo == 'spa' else '/equipe',
           'LOGO': logo, 'LIST_HIDDEN': lista_oculta, 'LIST_HTML': lista_html(posts, modo) if lista_oculta == '' else '',
           'POSTS_HTML': posts_html, 'CALC_URL': calc, 'FORM_URL': json.dumps(CFG.get('form_url', '') if modo != 'spa' else ''), 'CALC_HTML': calc_html(calc), 'SHARE_BASE': share, 'FOOTER': rodape(logo)}
    if modo == 'spa':
        fontes = {os.path.basename(f): open(f, encoding='utf-8').read() for f in FONTES}
        rep['POSTS_HTML'] += '\n<script type="application/json" id="fontes-md">' + json.dumps(fontes, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    for k, v in rep.items():
        tpl = tpl.replace('{{' + k + '}}', v)
    tpl = tpl.replace('{{HOME_EQUIPE}}', rep['HOME_EQUIPE'])
    return tpl


def extras(posts, dest):
    hoje = datetime.now()
    urls = [f'{SITE}/blog/', f'{SITE}/equipe'] + [canon(p) for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
        f'  <url><loc>{u}</loc><lastmod>{(p["data"] if p else hoje):%Y-%m-%d}</lastmod></url>\n'
        for u, p in zip(urls, [None, None] + posts)) + '</urlset>\n'
    open(os.path.join(dest, 'blog', 'sitemap.xml'), 'w').write(sm)
    robots = '\n'.join(f'User-agent: {b}\nAllow: /\n' for b in
                       ['*', 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
                        'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'Bingbot']) + f'\nSitemap: {SITE}/blog/sitemap.xml\n'
    os.makedirs(os.path.join(dest, 'para-lumino-raiz-do-site'), exist_ok=True)
    open(os.path.join(dest, 'para-lumino-raiz-do-site', 'robots-acrescentar.txt'), 'w').write(robots)
    llms = [f'# Camargo Lourenço Advogados – Blog jurídico', '',
            '> Escritório de advocacia em Barueri/SP. O blog responde, em linguagem simples, às primeiras dúvidas sobre INSS '
            '(previdenciário e assistencial), direitos do trabalhador e questões tributárias do contribuinte (execução fiscal e isenção de imposto de renda). Conteúdo informativo, sem promessa de resultado.', '',
            '## Autoras',
            '- Aline Camargo – Advogada Previdenciária e Tributária - Camargo Lourenço Advogados',
            '- Lislie Lourenço – Advogada Trabalhista e Cível - Camargo Lourenço Advogados', '',
            '## Contato do escritório',
            '- Telefone: (11) 4382-4240 · WhatsApp previdenciário e tributário: (11) 96335-3678 · WhatsApp trabalhista: (11) 98034-7924',
            '- E-mail: contato@camargolourenco.adv.br · Endereço: Av. Henriqueta Mendes Guerra, 1330, sala 305, Barueri/SP', '']
    for area in AREAS:
        llms.append(f'## {AUTORAS[area]["area_txt"]}')
        llms += [f'- [{p["titulo"]}]({canon(p)}): {p["resumo"]}' for p in posts if p['area'] == area]
        llms.append('')
    open(os.path.join(dest, 'para-lumino-raiz-do-site', 'llms.txt'), 'w').write('\n'.join(llms))
    open(os.path.join(dest, 'blog', 'llms.txt'), 'w').write('\n'.join(llms))
    rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
           '<title>Blog jurídico – Camargo Lourenço Advogados</title>', f'<link>{SITE}/blog/</link>',
           '<description>Respostas práticas sobre INSS e direitos do trabalhador.</description><language>pt-br</language>']
    for p in posts:
        rss.append(f'<item><title>{esc(p["titulo"])}</title><link>{canon(p)}</link><guid>{canon(p)}</guid>'
                   f'<pubDate>{p["publicado"]:%a, %d %b %Y} 08:00:00 -0300</pubDate><description>{esc(p["resumo"])}</description>'
                   f'<author>contato@camargolourenco.adv.br ({AUTORAS[p["area"]]["nome"]})</author></item>')
    rss.append('</channel></rss>')
    open(os.path.join(dest, 'blog', 'feed.xml'), 'w').write('\n'.join(rss))


FONTES = []


def recuperar(html_path):
    """Extrai os .md guardados numa página já publicada para a pasta posts/."""
    s = open(html_path, encoding='utf-8').read()
    m = re.search(r'<script type="application/json" id="fontes-md">(.*?)</script>', s, re.S)
    fontes = json.loads(m.group(1).replace('<\\/', '</'))
    os.makedirs(os.path.join(BASE, 'posts'), exist_ok=True)
    for nome, txt in fontes.items():
        open(os.path.join(BASE, 'posts', nome), 'w', encoding='utf-8').write(txt)
    print(len(fontes), 'textos recuperados')


# ---------- newsletter (e-mail com os textos completos do dia) ----------
NAVY, GOLD, GOLDINK, MUTED = '#013366', '#E9DB88', '#9A7B1F', '#3E5068'
FONT = "Comfortaa,Arial,Helvetica,sans-serif"
SERIF = "'Marcellus SC',Georgia,'Times New Roman',serif"


def com_faq(corpo, faq):
    m = re.search(r'<h[23][^>]*>Base legal</h[23]>', corpo)
    return corpo[:m.start()] + faq + corpo[m.start():] if (m and faq) else corpo + faq


def email_inline(h):
    """Converte o HTML do artigo em HTML com estilos inline (compatível com Gmail e Outlook)."""
    rep = [
        (r'<h2[^>]*>', f'<h3 style="font-family:{SERIF};font-weight:normal;font-size:20px;color:{NAVY};margin:26px 0 10px">'),
        (r'</h2>', '</h3>'),
        (r'<p>', f'<p style="margin:0 0 14px;font-size:16px;line-height:1.6;color:{NAVY}">'),
        (r'<ul>', f'<ul style="margin:0 0 14px;padding-left:22px;color:{NAVY}">'),
        (r'<ol>', f'<ol style="margin:0 0 14px;padding-left:22px;color:{NAVY}">'),
        (r'<li>', '<li style="margin:0 0 8px;font-size:16px;line-height:1.6">'),
    ]
    for a, c in rep:
        h = re.sub(a, c, h)
    return h


def newsletter(posts):
    if not posts:
        return None
    dia = max(p['publicado'] for p in posts)
    ordem = {a: i for i, a in enumerate(AREAS)}
    hoje = sorted([p for p in posts if p['publicado'] == dia], key=lambda p: ordem[p['area']])
    logo = f'{SITE}/blog/assets/logo.png'
    indice = ''.join(f'<li style="margin:0 0 6px;font-size:15px;line-height:1.5"><a href="#{p["slug"]}" style="color:{NAVY};text-decoration:none">'
                     f'<b style="color:{GOLDINK}">{AUTORAS[p["area"]]["area_txt"]}:</b> {esc(p["titulo"])}</a></li>' for p in hoje)
    arts = []
    for p in hoje:
        a = AUTORAS[p['area']]
        arts.append(f'''<tr><td style="padding:28px 32px;background:#FFFFFF;border-top:6px solid {GOLD}" id="{p["slug"]}">
<p style="margin:0 0 6px;font-size:13px;font-weight:bold;color:{GOLDINK};text-transform:uppercase;letter-spacing:1px">{a["area_txt"]}</p>
<h2 style="font-family:{SERIF};font-weight:normal;font-size:26px;line-height:1.25;color:{NAVY};margin:0 0 8px">{esc(p["titulo"])}</h2>
<p style="margin:0 0 18px;font-size:14px;color:{MUTED}">Por {a["nome"]}, {a["cargo"]}</p>
<div style="background:#F2F2F2;border-left:5px solid {GOLDINK};padding:14px 18px;margin:0 0 8px">
<p style="margin:0 0 6px;font-family:{SERIF};font-size:16px;color:{GOLDINK}">Resposta rápida</p>{email_inline(p["resposta_html"]).replace("margin:0 0 14px", "margin:0")}</div>
<p style="margin:18px 0 0"><a href="{canon(p)}" style="display:inline-block;background:{NAVY};color:#FFFFFF;text-decoration:none;font-weight:bold;font-size:15px;padding:12px 20px;border-radius:4px">Ler o texto completo no blog</a></p>
</td></tr><tr><td style="height:14px;line-height:14px;font-size:0">&nbsp;</td></tr>''')
    html_ = f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(CFG["newsletter_assunto"])}</title>
<link href="https://fonts.googleapis.com/css2?family=Marcellus+SC&family=Comfortaa:wght@400;700&display=swap" rel="stylesheet">
<style>@import url('https://fonts.googleapis.com/css2?family=Marcellus+SC&family=Comfortaa:wght@400;700&display=swap');</style></head>
<body style="margin:0;padding:0;background:#E8EDF3">
<div style="display:none;max-height:0;overflow:hidden">{esc(" · ".join(p["titulo"] for p in hoje))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#E8EDF3"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;font-family:{FONT};color:{NAVY}">
<tr><td style="background:{NAVY};padding:20px 32px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td valign="middle" align="left"><img src="{SITE}/blog/assets/newsletter-titulo.png" alt="Blog Jurídico" width="170" style="display:block;width:170px;height:auto;border:0;font-family:{SERIF};font-size:24px;color:#FFFFFF">
<p style="margin:4px 0 0;font-size:14px;color:{GOLD}">{data_br(dia)}</p></td>
<td valign="middle" align="right" width="150"><img src="{logo}" alt="Camargo Lourenço Advogados" width="140" style="display:block;width:140px;height:auto;border:0;margin-left:auto"></td>
</tr></table></td></tr>
<tr><td style="background:#FFFFFF;padding:22px 32px"><p style="margin:0 0 10px;font-size:16px;color:{NAVY}">Olá, {{{{NOME}}}}! Estes são os textos de hoje:</p><ul style="margin:0;padding-left:20px">{indice}</ul></td></tr>
<tr><td style="height:14px;line-height:14px;font-size:0">&nbsp;</td></tr>
{"".join(arts)}
<tr><td style="background:#FFFFFF;padding:20px 32px" align="center"><p style="margin:0 0 12px;font-size:15px;color:{NAVY}">Veja todas as dúvidas já respondidas e as calculadoras:</p>
<a href="{SITE}/blog/" style="display:inline-block;background:{GOLD};color:{NAVY};text-decoration:none;font-weight:bold;font-size:15px;padding:12px 22px;border-radius:4px">Acessar o Blog Jurídico</a>
<p style="margin:16px 0 0;font-size:12px;line-height:1.5;color:{MUTED}">Os textos são informativos e não substituem a análise de um advogado. Cada caso tem detalhes que podem mudar a resposta.</p></td></tr>
<tr><td style="height:14px;line-height:14px;font-size:0">&nbsp;</td></tr>
<tr><td style="background:{NAVY};padding:22px 32px;font-size:13px;line-height:1.6;color:#FFFFFF">
<p style="margin:0 0 6px">Camargo &amp; Lourenço Advogados · OAB/SP 36.265</p>
<p style="margin:0 0 6px">(11) 4382-4240 · WhatsApp (11) 96335-3678 (previdenciário e tributário) · WhatsApp (11) 98034-7924 (trabalhista)</p>
<p style="margin:0 0 12px">Av. Henriqueta Mendes Guerra, 1330 - Sala 305 - 3º Andar - Barueri/SP</p>
<p style="margin:0;color:#B4C6D9">Você recebe este e-mail porque se inscreveu no blog do escritório. <a href="{{{{SAIR}}}}" style="color:{GOLD}">Cancelar a inscrição</a>.</p>
</td></tr></table></td></tr></table></body></html>'''
    assunto = f'{CFG["newsletter_assunto"]} ({dia:%d/%m})'
    return dia, assunto, html_


def gravar_newsletter(posts, pasta):
    r = newsletter(posts)
    if not r:
        return
    dia, assunto, html_ = r
    os.makedirs(pasta, exist_ok=True)
    open(os.path.join(pasta, 'ultima.html'), 'w', encoding='utf-8').write(html_)
    open(os.path.join(pasta, f'{dia:%Y-%m-%d}.html'), 'w', encoding='utf-8').write(html_)
    json.dump({'data': f'{dia:%Y-%m-%d}', 'assunto': assunto}, open(os.path.join(pasta, 'ultima.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('newsletter', f'{dia:%d/%m/%Y}', len(html_.encode()) // 1024, 'kB')


import shutil


def main():
    if len(sys.argv) > 2 and sys.argv[1] == 'recuperar':
        return recuperar(sys.argv[2])
    modo = sys.argv[1] if len(sys.argv) > 1 else 'spa'
    pasta = os.path.join(BASE, 'posts')
    global FONTES
    FONTES = [os.path.join(pasta, f) for f in sorted(os.listdir(pasta)) if f.endswith('.md')]
    posts = [ler_post(f) for f in FONTES]
    posts.sort(key=lambda p: (p['publicado'], p['data']), reverse=True)
    logo = open(os.path.join(BASE, 'logo.txt')).read().strip()
    os.makedirs(os.path.join(BASE, 'dist'), exist_ok=True)
    if modo == 'spa':
        out = os.path.join(BASE, 'dist', 'blog.html')
        open(out, 'w', encoding='utf-8').write(montar(posts, 'spa', logo=logo))
        print(out, len(posts), 'textos')
        gravar_newsletter(posts, os.path.join(BASE, 'dist', 'newsletter'))
    else:
        dest = os.path.join(BASE, 'dist', 'site')
        os.makedirs(os.path.join(dest, 'blog'), exist_ok=True)
        logo_url = '/blog/assets/logo.png'
        open(os.path.join(dest, 'blog', 'index.html'), 'w', encoding='utf-8').write(montar(posts, 'site', logo=logo_url))
        for p in posts:
            d = os.path.join(dest, 'blog', p['slug'])
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(montar(posts, 'site', p, logo=logo_url))
        os.makedirs(os.path.join(dest, 'blog', 'equipe'), exist_ok=True)
        open(os.path.join(dest, 'blog', 'equipe', 'index.html'), 'w', encoding='utf-8').write(montar(posts, 'site', 'equipe', logo=logo_url))
        os.makedirs(os.path.join(dest, 'blog', 'assets'), exist_ok=True)
        shutil.copytree(os.path.join(BASE, 'assets', 'equipe'), os.path.join(dest, 'blog', 'assets', 'equipe'), dirs_exist_ok=True)
        import base64
        shutil.copy(os.path.join(BASE, 'assets', 'newsletter-titulo.png'), os.path.join(dest, 'blog', 'assets', 'newsletter-titulo.png'))
        open(os.path.join(dest, 'blog', 'assets', 'logo.png'), 'wb').write(base64.b64decode(logo.split(',', 1)[1]))
        extras(posts, dest)
        gravar_newsletter(posts, os.path.join(dest, 'blog', 'newsletter'))
        print(dest, len(posts), 'textos')


if __name__ == '__main__':
    main()
