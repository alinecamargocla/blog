"""Monta o e-mail de aprovação de um rascunho (texto completo + botões)."""
import html, os, re
from comum import AREA_TXT
import build

NAVY, GOLD, GOLDINK, MUTED = '#013366', '#E9DB88', '#9A7B1F', '#3E5068'
F = 'Arial,Helvetica,sans-serif'
S = "Georgia,'Times New Roman',serif"


def botao(url, texto, fundo, cor='#FFFFFF'):
    return (f'<a href="{url}" style="display:inline-block;margin:0 8px 8px 0;background:{fundo};color:{cor};text-decoration:none;'
            f'font-weight:bold;font-size:15px;padding:12px 20px;border-radius:4px;font-family:{F}">{texto}</a>')


def montar(caminho_md, item, avisos, url_script):
    p = build.ler_post(caminho_md)
    txt = open(caminho_md, encoding='utf-8').read()
    curta = txt.split('# Versão curta', 1)[1].strip() if '# Versão curta' in txt else ''
    conferir = list(dict.fromkeys(re.findall(r'\[CONFERIR[^\]]*\]', txt)))
    avisos = [a for a in avisos if 'CONFERIR' not in a]
    faq = ''
    if p['faq']:
        faq = (f'<h3 style="font-family:{S};font-weight:normal;font-size:20px;color:{NAVY};margin:26px 0 10px">Perguntas frequentes</h3>'
               + ''.join(f'<p style="margin:0 0 4px;font-size:16px;color:{NAVY}"><b>{html.escape(q)}</b></p>'
                         f'<p style="margin:0 0 14px;font-size:16px;line-height:1.6;color:{NAVY}">{html.escape(r)}</p>' for q, r in p['faq']))
    corpo = build.com_faq(build.email_inline(p['corpo_html']), faq)
    t = item['token']
    lnk = lambda d: f'{url_script}?rev={t}&d={d}'
    alertas = ''
    if conferir or avisos:
        lis = ''.join(f'<li>{html.escape(c)}</li>' for c in conferir) + ''.join(f'<li>{html.escape(a)}</li>' for a in avisos)
        alertas = (f'<div style="background:#FFF6D6;border-left:5px solid {GOLDINK};padding:12px 16px;margin:0 0 18px;font-size:14px;color:{NAVY}">'
                   f'<b>Pontos para conferir antes de aprovar:</b> (itens [CONFERIR] precisam ser resolvidos: use “Pedir ajuste” e informe o dado correto)<ul style="margin:6px 0 0;padding-left:20px">{lis}</ul></div>')
    versao = f' (versão {item["versao"]}, com o ajuste pedido)' if item.get('versao', 1) > 1 else ''
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"></head><body style="margin:0;background:#E8EDF3">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;font-family:{F};color:{NAVY}">
<tr><td style="background:{NAVY};padding:18px 28px;color:#FFFFFF"><p style="margin:0;font-family:{S};font-size:22px">Blog Jurídico · aprovação</p>
<p style="margin:4px 0 0;font-size:14px;color:{GOLD}">{AREA_TXT[item["area"]]} · pauta de {item["data_pauta"][8:10]}/{item["data_pauta"][5:7]}{versao}</p></td></tr>
<tr><td style="background:#FFFFFF;padding:22px 28px">
<p style="margin:0 0 14px;font-size:15px">Este texto só vai ao ar depois da sua aprovação.</p>
{botao(lnk("aprovar"), "Aprovar e publicar", "#1f9d55")}{botao(lnk("ajustar"), "Pedir ajuste", NAVY)}{botao(lnk("recusar"), "Não publicar", "#FFFFFF", NAVY)}
</td></tr>
<tr><td style="background:#FFFFFF;padding:6px 28px 26px;border-top:6px solid {GOLD}">
{alertas}
<p style="margin:14px 0 6px;font-size:13px;font-weight:bold;color:{GOLDINK};text-transform:uppercase;letter-spacing:1px">{AREA_TXT[item["area"]]}</p>
<h1 style="font-family:{S};font-weight:normal;font-size:28px;line-height:1.25;margin:0 0 10px">{html.escape(p["titulo"])}</h1>
<p style="margin:0 0 16px;font-size:13px;color:{MUTED}"><b>Resumo para busca:</b> {html.escape(p["resumo"])}<br><b>Palavras-chave:</b> {html.escape(p["chaves"])}</p>
<div style="background:#F2F2F2;border-left:5px solid {GOLDINK};padding:14px 18px;margin:0 0 8px"><p style="margin:0 0 6px;font-family:{S};color:{GOLDINK}">Resposta rápida</p>
{build.email_inline(p["resposta_html"]).replace("margin:0 0 14px", "margin:0")}</div>
{corpo}
<h3 style="font-family:{S};font-weight:normal;font-size:20px;margin:26px 0 10px">Versão curta para as redes</h3>
<pre style="white-space:pre-wrap;font-family:{F};font-size:14px;line-height:1.5;background:#F2F2F2;padding:14px 16px;margin:0">{html.escape(curta)}</pre>
</td></tr>
<tr><td style="background:#FFFFFF;padding:18px 28px;border-top:1px solid #DDE3EA">
{botao(lnk("aprovar"), "Aprovar e publicar", "#1f9d55")}{botao(lnk("ajustar"), "Pedir ajuste", NAVY)}{botao(lnk("recusar"), "Não publicar", "#FFFFFF", NAVY)}
<p style="margin:8px 0 0;font-size:12px;color:{MUTED}">Ao clicar, abre uma página para confirmar. Textos aprovados entram no blog no mesmo dia, ou no dia seguinte se a área já tiver texto publicado hoje.</p>
</td></tr></table></td></tr></table></body></html>'''
