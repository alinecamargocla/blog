"""Publica os textos aprovados: no máximo um por área por dia, do mais antigo para o mais novo."""
import os, re, shutil
from comum import *


def main():
    data = hoje()
    fila = ler_fila()
    mudou = False
    for area in AREA_TXT:
        if any(i['area'] == area and i.get('publicado_em', '')[:10] == data for i in fila):
            continue  # a área já teve texto publicado hoje; o próximo aprovado fica para amanhã
        aprovados = sorted([i for i in fila if i['area'] == area and i['status'] == 'aprovado'],
                           key=lambda i: (i['data_pauta'], i.get('decidido_em', '')))
        if not aprovados:
            continue
        item = aprovados[0]
        md = open(os.path.join(RAIZ, item['arquivo']), encoding='utf-8').read()
        md = re.sub(r'^Atualizado em:.*$', f'Atualizado em: {data[8:10]}/{data[5:7]}/{data[:4]}', md, count=1, flags=re.M)
        titulo = re.search(r'^# (.+)$', md, re.M).group(1)
        slug = slugify(titulo)
        existentes = {re.sub(r'^\d{4}-\d{2}-\d{2}-', '', f[:-3]) for f in os.listdir(os.path.join(RAIZ, 'posts'))}
        base, n = slug, 2
        while slug in existentes:
            slug = f'{base}-{n}'; n += 1
        destino = f'posts/{data}-{slug}.md'
        open(os.path.join(RAIZ, destino), 'w', encoding='utf-8').write(md)
        item.update(status='publicado', publicado_em=data + agora().strftime('T%H:%M'), post=destino,
                    url=f'{CFG["site"].rstrip("/")}/blog/{slug}/')
        print('publicado:', destino); mudou = True
        notificar('publicado', {'token': item['token'], 'area': area, 'titulo': titulo, 'url': item['url'],
                                'destinatario': CFG['aprovadores'][area]})
    if mudou:
        gravar_fila(fila)


if __name__ == '__main__':
    main()
