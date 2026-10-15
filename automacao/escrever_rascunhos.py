"""Rotina da madrugada: escreve os rascunhos do dia (cronograma) e pede aprovação por e-mail."""
import os, sys
from comum import *
import email_aprovacao


def pedir_aprovacao(item, avisos):
    caminho = os.path.join(RAIZ, item['arquivo'])
    url = os.environ.get('APPS_SCRIPT_URL', 'https://script.google.com/(configurar)')
    html_ = email_aprovacao.montar(caminho, item, avisos, url)
    import build
    titulo = build.ler_post(caminho)['titulo']
    notificar('rascunho', {'token': item['token'], 'area': item['area'], 'titulo': titulo,
                           'destinatario': CFG['aprovadores'][item['area']], 'data_pauta': item['data_pauta'],
                           'assunto': f'Aprovar texto do blog ({AREA_TXT[item["area"]]}): {titulo}', 'html': html_})


def main():
    data = sys.argv[1] if len(sys.argv) > 1 else hoje()
    crono = json.load(open(os.path.join(RAIZ, 'cronograma', 'cronograma.json'), encoding='utf-8'))
    fila = ler_fila()
    feitos = {(i['data_pauta'], i['area']) for i in fila}
    for pauta in [c for c in crono if c['data'] == data and c['status'] == 'Aprovado']:
        if (data, pauta['area']) in feitos:
            print('já escrito:', data, pauta['area']); continue
        token = novo_token()
        arquivo = f'rascunhos/{data}-{pauta["area"]}-{token[:8]}.md'
        pedido = (f'Escreva o texto do blog de hoje.\nÁrea: {AREA_TXT[pauta["area"]].lower()}\n'
                  f'Pauta aprovada no cronograma: {pauta["pauta"]}\nData do texto (linha "Atualizado em"): '
                  f'{data[8:10]}/{data[5:7]}/{data[:4]}')
        md, erros, avisos = escrever_com_verificacao([{'role': 'user', 'content': pedido}], os.path.join(RAIZ, arquivo))
        item = {'token': token, 'area': pauta['area'], 'data_pauta': data, 'pauta': pauta['pauta'], 'arquivo': arquivo,
                'status': 'aguardando', 'versao': 1, 'criado_em': agora().isoformat(timespec='minutes'),
                'erros_verificador': erros}
        fila.append(item); gravar_fila(fila)
        pedir_aprovacao(item, erros + avisos)
        print('rascunho:', arquivo)


if __name__ == '__main__':
    main()
