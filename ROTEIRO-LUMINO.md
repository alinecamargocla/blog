# Roteiro para a Lumino — Blog Jurídico em www.camargolourenco.adv.br/blog

O blog é gerado e hospedado à parte, no **Netlify** (endereço `SEU-BLOG.netlify.app`, informado pelo escritório). O site principal continua na Vercel, sem mudanças além do proxy abaixo. Ele precisa aparecer **dentro do domínio principal, em /blog**, sem redirecionamento.

## 1. Proxy de /blog no Next.js
Em `next.config.js` (ou `.mjs`), acrescentar:
```js
async rewrites() {
  return [
    { source: '/blog', destination: 'https://SEU-BLOG.netlify.app/blog/' },
    { source: '/blog/:path*', destination: 'https://SEU-BLOG.netlify.app/blog/:path*' },
    { source: '/equipe', destination: 'https://SEU-BLOG.netlify.app/blog/equipe/' },
  ];
},
```
Tudo do blog fica sob `/blog/` (páginas, imagens em `/blog/assets/`, `sitemap.xml`, `feed.xml`, `llms.txt` e newsletter). A página **/equipe** (advogadas e escritório) também é gerada pelo blog e aparece no endereço `www.camargolourenco.adv.br/equipe`. Se o site tiver um link "Equipe" ou "Quem somos", ele pode apontar para `/equipe`.

## 2. Raiz do site
- **robots.txt**: acrescentar as linhas do arquivo `para-lumino-raiz-do-site/robots-acrescentar.txt` (liberam os robôs das IAs e apontam o sitemap `https://www.camargolourenco.adv.br/blog/sitemap.xml`).
- **llms.txt**: publicar o arquivo `para-lumino-raiz-do-site/llms.txt` em `https://www.camargolourenco.adv.br/llms.txt` (ou somar ao existente).
- **Menu**: incluir o link "Blog" (`/blog`) no menu e no rodapé do site.

## 3. Outras páginas
- Subir a versão atualizada da LP trabalhista: ela abre a calculadora certa pelos links `/trabalhista#calc-resc`, `#calc-fgts`, `#calc-seg`, `#calc-he`, `#calc-fer` e `#calc-13`, usados pelo blog.
- A LP `/bpcloas` deve manter a seção com `id="calculadora"` (link do blog: `/bpcloas#calculadora`).

## 4. Depois de no ar
- Google Search Console: enviar o sitemap `https://www.camargolourenco.adv.br/blog/sitemap.xml`.
- Conferir SPF, DKIM e DMARC do domínio camargolourenco.adv.br (a newsletter e os e-mails de aprovação saem do Gmail contato@).
