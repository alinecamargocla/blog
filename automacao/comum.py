"""Funções comuns da automação do Blog Jurídico CLA (rodam no GitHub Actions)."""
import json, os, re, subprocess, sys, unicodedata, urllib.request, uuid
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
FUSO = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)
CFG = json.load(open(os.path.join(RAIZ, 'config.json'), encoding='utf-8'))
FILA = os.path.join(RAIZ, 'rascunhos', 'fila.json')
AREA_TXT = {'previdenciario': 'Previdenciário', 'trabalhista': 'Trabalhista', 'tributario': 'Tributário'}


def agora():
    return datetime.now(FUSO)


def hoje():
    return os.environ.get('DATA_HOJE') or agora().strftime('%Y-%m-%d')


def slugify(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > 60:
        s = s[:60].rsplit('-', 1)[0]
    return s


def novo_token():
    return uuid.uuid4().hex


def ler_fila():
    return json.load(open(FILA, encoding='utf-8'))


def gravar_fila(fila):
    json.dump(fila, open(FILA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def ler(caminho):
    return open(os.path.join(RAIZ, caminho), encoding='utf-8').read()


# ---------------- Claude (API da Anthropic) ----------------
def instrucoes_skill():
    partes = [ler('skill/SKILL.md')]
    for f in ['regras-oab.md', 'linguagem.md', 'modelo-artigo.md', 'observacoes-da-pratica.md']:
        partes.append(f'\n\n=== references/{f} ===\n' + ler('skill/references/' + f))
    partes.append('''

=== Regras desta execução automática ===
- Você está rodando sem acesso à internet. Não invente números de lei, súmula ou tema. Quando não tiver certeza de um dado, marque [CONFERIR: o que conferir] no texto.
- Responda SOMENTE com o conteúdo do arquivo .md do artigo, no formato do modelo, começando por "# " e terminando na assinatura e na versão curta. Sem comentários antes ou depois.
- Inclua obrigatoriamente as linhas "Resumo para busca:", "Palavras-chave:", "Área:" e "Atualizado em:".
- Não publique nada: o texto vai para aprovação da advogada responsável.''')
    return ''.join(partes)


def claude(mensagens, max_tokens=6000):
    if os.environ.get('MODO_TESTE'):
        return os.environ['MODO_TESTE_RESPOSTA']
    corpo = json.dumps({'model': CFG.get('modelo', 'claude-sonnet-5-5'), 'max_tokens': max_tokens,
                        'system': instrucoes_skill(), 'messages': mensagens}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=corpo, headers={
        'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        dados = json.load(r)
    return ''.join(b.get('text', '') for b in dados['content'] if b.get('type') == 'text').strip()


def verificar(caminho):
    """Roda o verificador da skill. Devolve (erros, avisos)."""
    r = subprocess.run([sys.executable, os.path.join(RAIZ, 'skill', 'scripts', 'checar_texto.py'), caminho],
                       capture_output=True, text=True)
    linhas = r.stdout.splitlines()
    return [l for l in linhas if l.startswith('ERRO')], [l for l in linhas if l.startswith('AVISO')]


def escrever_com_verificacao(mensagens, caminho):
    """Pede o texto ao Claude, verifica e, se houver erro, pede uma correção."""
    md = limpar(claude(mensagens))
    open(caminho, 'w', encoding='utf-8').write(md)
    erros, avisos = verificar(caminho)
    if erros:
        mensagens = mensagens + [{'role': 'assistant', 'content': md}, {'role': 'user', 'content':
            'O verificador da skill apontou estes erros. Corrija e devolva o arquivo completo:\n' + '\n'.join(erros)}]
        md = limpar(claude(mensagens))
        open(caminho, 'w', encoding='utf-8').write(md)
        erros, avisos = verificar(caminho)
    return md, erros, avisos


def limpar(md):
    md = re.sub(r'^```(?:markdown|md)?\s*|\s*```$', '', md.strip())
    i = md.find('# ')
    return (md[i:] if i > 0 else md).strip() + '\n'


# ---------------- Aviso ao script do Google ----------------
def notificar(acao, dados):
    url = os.environ.get('APPS_SCRIPT_URL')
    if not url:
        print('APPS_SCRIPT_URL não configurada; aviso não enviado:', acao)
        return
    corpo = json.dumps({'acao': acao, 'segredo': os.environ.get('APPS_SCRIPT_SEGREDO', ''), **dados}).encode()
    req = urllib.request.Request(url, data=corpo, headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        print('aviso enviado:', acao, r.status)
