#!/usr/bin/env python3
"""Verifica um texto do blog CLA: promessa de resultado, regras da OAB,
juridiquês e legibilidade. Uso: python checar_texto.py arquivo.md"""
import re, sys, unicodedata

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

ERROS = {  # promessa de resultado / OAB
    r'\bgarantid[oa]s?\b|\bgaranta\b|\bgarantimos\b': 'promessa de resultado',
    r'\bvoce vai (ganhar|receber|conseguir)\b': 'promessa de resultado',
    r'\b(ganhe|receba) (ja|agora|sua|seu)\b': 'promessa de resultado',
    r'\b100 ?%': 'promessa de resultado',
    r'\bcom certeza (vai|voce)\b|\bcerteza de (ganhar|receber)\b': 'promessa de resultado',
    r'\bcausa ganha\b|\bsucesso garantido\b': 'promessa de resultado',
    r'\bconsulta (gratis|gratuita)\b|\bsem custo\b|\bde graca\b': 'captação/mercantilização (OAB)',
    r'\bso paga se ganhar\b|\bhonorarios? de\b|\bdesconto (nos|em|de) honorario|\b\d+ ?% de desconto|\bpromocao\b': 'captação/mercantilização (OAB)',
    r'\bultimas vagas\b|\bcorra\b|\bnao perca\b|\bchame (ja|agora)\b|\bligue (ja|agora)\b': 'urgência/apelo (OAB)',
    r'\bo melhor advogad|\bmelhor escritorio\b|\bespecialista n': 'autopromoção comparativa (OAB)',
    r'\burgente\b|\bbomba\b|\bnao quer que voce saiba\b': 'sensacionalismo (OAB)',
    r'\bnosso cliente\b|\bnossa cliente\b|\bconseguimos para\b|\bganhamos\b': 'cita cliente/resultado (OAB)',
    r'\(?\d{2}\)? ?9?\d{4}-\d{4}|(pelo|no|nosso) whatsapp|@camargolourenco|www\.|\.adv\.br|analise o seu caso': 'contato no texto — telefone, e-mail, site e convite ficam só no rodapé',
    r'\bvoce tem direito\b': 'afirmação categórica — prefira "pode ter direito"',
}
AVISOS = {
    r'\bespecialista\b': '"especialista" só com título acadêmico',
    r'\brequerimento administrativo\b': 'juridiquês → "pedido no INSS"',
    r'\bindeferiment': 'juridiquês → "negativa"',
    r'\bverbas rescisorias\b': 'juridiquês → explique "dinheiro da rescisão"',
    r'\boutrossim\b|\bdestarte\b|\bademais\b|\benseja': 'juridiquês',
    r'\bprescricional\b|\bprescricao\b': 'explique como "prazo para entrar com o processo"',
    r'\bsegurad[oa]\b': 'prefira "você" / "quem contribui"',
    r'\bobrigad[oa] a pagar\b': 'tom categórico — prefira "a lei prevê"',
    r'R\$ ?\d': 'valor em reais — confira se não soa como promessa e se está atualizado',
}

def main(path):
    txt = open(path, encoding='utf-8').read()
    n = norm(txt)
    erros = avisos = 0
    for pat, msg in ERROS.items():
        for m in re.finditer(pat, n):
            erros += 1
            print(f'ERRO  | {msg}: "...{n[max(0,m.start()-30):m.end()+30].strip()}..."')
    for pat, msg in AVISOS.items():
        for m in re.finditer(pat, n if not pat.startswith('R') else txt):
            avisos += 1
            print(f'AVISO | {msg}')
            break
    # texto atemporal: ano no título ou fora da base legal
    tit = re.search(r'^# (.+)$', txt, re.M)
    if tit and re.search(r'\b20\d\d\b', tit.group(1)):
        erros += 1
        print('ERRO  | ano no título: o texto precisa ser atemporal')
    corpo_sem_base = re.split(r'## Base legal', txt)[0]
    corpo_sem_base = re.sub(r'^Atualizado em:.*$', '', corpo_sem_base, flags=re.M)
    for m in re.finditer(r'\b(em|de|ano de|até) 20\d\d\b', corpo_sem_base, re.I):
        avisos += 1
        print(f'AVISO | ano no texto ("{m.group(0)}"): prefira redação atemporal')
        break
    # legibilidade
    corpo = re.sub(r'[#*|>`\-]', ' ', txt)
    frases = [f for f in re.split(r'[.!?:]\s|\n', corpo) if f.strip()]
    longas = [f.strip() for f in frases if len(f.split()) > 28]
    for f in longas[:5]:
        avisos += 1
        print(f'AVISO | frase longa ({len(f.split())} palavras): "{f[:80]}..."')
    palavras = len(corpo.split())
    print(f'INFO  | {palavras} palavras, {len(longas)} frases longas')
    for item, pat in [('aviso "não substitui a análise"', r'nao substitui'),
                      ('assinatura (Advogada ... - Camargo Lourenço Advogados)', r'advogada (previdenciaria|trabalhista|tributaria) - camargo lourenco advogados'),
                      ('perguntas frequentes', r'perguntas frequentes'),
                      ('data de atualização', r'atualizado em')]:
        if not re.search(pat, n):
            print(f'AVISO | falta: {item}'); avisos += 1
    if '[conferir' in n:
        print('AVISO | há itens [CONFERIR] pendentes')
    print(f'RESULTADO | {erros} erro(s), {avisos} aviso(s)')
    sys.exit(1 if erros else 0)

if __name__ == '__main__':
    main(sys.argv[1])
