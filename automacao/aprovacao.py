"""Recebe a decisão da advogada (vinda do script do Google): aprovar, ajustar ou recusar."""
import os, sys, json
from comum import *
from escrever_rascunhos import pedir_aprovacao
import publicar
import re

SECAO = {'previdenciario': '## Previdenciário', 'trabalhista': '## Trabalhista', 'tributario': '## Tributário'}


def guardar_observacao(item, obs):
    """Copia a observação para a base da skill, para ser reaproveitada em textos futuros do mesmo tema."""
    caminho = os.path.join(RAIZ, 'skill', 'references', 'observacoes-da-pratica.md')
    txt = open(caminho, encoding='utf-8').read()
    linha = f'- ({item["pauta"]}) ' + ' '.join(obs.split())
    i = txt.find(SECAO[item['area']])
    j = txt.find('\n## ', i + 3)
    j = len(txt) if j < 0 else j
    txt = txt[:j].rstrip('\n') + '\n' + linha + '\n' + ('\n' if j < len(txt) else '') + txt[j:].lstrip('\n')
    open(caminho, 'w', encoding='utf-8').write(txt)


def main():
    dados = json.loads(os.environ.get('PAYLOAD') or sys.argv[1])
    token, decisao = dados['token'], dados['decisao']
    fila = ler_fila()
    item = next((i for i in fila if i['token'] == token), None)
    if not item or item['status'] != 'aguardando':
        print('token inexistente ou já decidido:', token); return
    item['decidido_em'] = agora().isoformat(timespec='minutes')
    item['decidido_por'] = dados.get('email', '')
    if decisao == 'aprovar':
        texto = open(os.path.join(RAIZ, item['arquivo']), encoding='utf-8').read()
        if '[CONFERIR' in texto:
            item['decidido_em'] = ''
            gravar_fila(fila)
            notificar('bloqueado', {'token': token, 'area': item['area'], 'destinatario': CFG['aprovadores'][item['area']],
                                    'motivo': 'O texto ainda tem pontos [CONFERIR]. Use "Pedir ajuste" e informe o dado correto.'})
            print('aprovação bloqueada: há [CONFERIR] no texto'); return
        obs = (dados.get('observacao') or '').strip()
        if obs:
            caminho = os.path.join(RAIZ, item['arquivo'])
            original = open(caminho, encoding='utf-8').read()
            bloco = '## Na prática do escritório\n' + obs + '\n\n'
            if '## Na prática do escritório' in original:
                novo = re.sub(r'## Na prática do escritório\n.*?(?=\n## )', bloco.rstrip('\n'), original, count=1, flags=re.S)
            else:
                novo = original.replace('## Perguntas frequentes', bloco + '## Perguntas frequentes', 1)
            open(caminho, 'w', encoding='utf-8').write(novo)
            erros, _ = verificar(caminho)
            if erros:
                open(caminho, 'w', encoding='utf-8').write(original)
                item['decidido_em'] = ''
                gravar_fila(fila)
                notificar('bloqueado', {'token': token, 'area': item['area'], 'destinatario': CFG['aprovadores'][item['area']],
                    'motivo': 'A observação da prática não passou no verificador da OAB: ' + '; '.join(erros) + '. O texto não foi publicado; aprove de novo com outra redação.'})
                print('observação bloqueada pelo verificador'); return
            guardar_observacao(item, obs)
        item['status'] = 'aprovado'
    elif decisao == 'recusar':
        item['status'] = 'recusado'
    elif decisao == 'ajustar':
        item['status'] = 'substituido'; item['comentario'] = dados.get('comentario', '')
        original = open(os.path.join(RAIZ, item['arquivo']), encoding='utf-8').read()
        novo = dict(item, token=novo_token(), status='aguardando', versao=item.get('versao', 1) + 1,
                    criado_em=agora().isoformat(timespec='minutes'), comentario='', decidido_em='', decidido_por='')
        novo['arquivo'] = item['arquivo'].rsplit('-', 1)[0] + f'-{novo["token"][:8]}.md'
        msgs = [{'role': 'user', 'content': 'Este é o rascunho atual do texto do blog:\n\n' + original +
                 '\n\nA advogada responsável pediu este ajuste:\n' + dados.get('comentario', '') +
                 '\n\nReescreva o arquivo completo aplicando o ajuste e mantendo todas as regras.'}]
        md, erros, avisos = escrever_com_verificacao(msgs, os.path.join(RAIZ, novo['arquivo']))
        novo['erros_verificador'] = erros
        fila.append(novo)
        gravar_fila(fila)
        pedir_aprovacao(novo, erros + avisos)
    gravar_fila(fila)
    publicar.main()


if __name__ == '__main__':
    main()
