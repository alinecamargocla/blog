---
name: blog-juridico-cla
description: Cria o conteúdo diário do blog do escritório Camargo Lourenço Advogados (Aline Camargo) em direito previdenciário, trabalhista e tributário (execução fiscal, isenção de IR e demais temas do contribuinte) — artigo prático em linguagem simples + versão curta para Instagram/LinkedIn/WhatsApp — para ser citado por buscadores e IAs, sempre dentro das regras de publicidade da OAB e sem prometer resultado. Use SEMPRE que a Aline pedir "post do dia", "artigo do blog", "notícia do dia", "conteúdo para o blog", "pauta da semana", "texto para Instagram/LinkedIn" sobre INSS, aposentadoria, auxílio-doença, BPC/LOAS, pensão por morte, rescisão, FGTS, horas extras, demissão, acidente de trabalho, execução fiscal, dívida ativa, isenção de IR, ITBI, ITCMD, ITR, INSS acima do teto, equiparação hospitalar, Simples Nacional ou qualquer dúvida previdenciária, trabalhista ou tributária, mesmo que ela não diga "blog" nem "skill".
---

# Blog Jurídico CLA — conteúdo diário

Objetivo: que a pessoa com uma dúvida (ou a IA a quem ela perguntou) encontre o texto, entenda o próximo passo e associe a resposta à advogada da área (Aline Camargo no previdenciário e no tributário, Lislie Lourenço no trabalhista) — e que fique fácil indicar o escritório a outra pessoa. O texto é útil por si só; a indicação vem da confiança, não de pressão.

## As três regras (inegociáveis)

1. **Prático e resolutivo.** Cada texto responde UMA dúvida real e termina com o que a pessoa deve fazer: documento a juntar, onde clicar no Meu INSS, prazo a observar, o que conferir no holerite. Nada de aula de teoria.
2. **Vocabulário do cliente.** Escreva como quem explica para a vizinha no portão. Frases curtas, voz ativa, "você". Termo técnico só se a pessoa vai encontrá-lo (ex.: "CNIS", "carência"), e explicado na hora entre parênteses. Detalhes em `references/linguagem.md`.
3. **Jamais prometer resultado.** Nada de "você vai ganhar", "garantido", "receba já", "100%", valores certos de indenização. Use "pode ter direito", "depende da análise", "em muitos casos". Regras da OAB em `references/regras-oab.md` — leia antes de escrever o primeiro texto da sessão.

## Fluxo

1. **Escolha a pauta.**
   - Se a Aline deu o tema, use-o.
   - Se não deu e houver busca na web disponível, procure novidade do dia (mudança do INSS, decisão do STJ/STF/TST/TNU, nova regra, prazo, pente-fino, reajuste) e traduza em dúvida prática: "O que muda para você?".
   - Sem novidade relevante, use `references/banco-de-pautas.md`, alternando previdenciário, trabalhista e tributário.
   - No tributário, escreva sempre do lado do contribuinte: o executado em execução fiscal, o aposentado/pensionista que busca isenção do imposto de renda, quem paga ITBI/ITCMD/ITR, quem contribuiu ao INSS acima do teto e, para empresas, equiparação hospitalar de clínicas e créditos de produtos monofásicos no Simples Nacional.
   - Siga o cronograma aprovado em `assets/cronograma.xlsx` (aba Cronograma; 13/10/2026 a 31/01/2027): no "post do dia", escreva e publique as três pautas da data de hoje (previdenciário, trabalhista e tributário), só as de Status "Aprovado". Se a Aline enviar uma planilha mais nova, ela vale no lugar desta. Depois de 31/01/2027, avise que é preciso montar um novo cronograma.
   - Formule a pauta como a pergunta que a pessoa digitaria: "Fui demitido grávida, e agora?", não "Estabilidade da gestante".
2. **Confira os fatos.** Valores (salário mínimo, teto do INSS, faixas de contribuição), prazos e regras mudam. Confirme em fonte oficial (gov.br/inss, planalto.gov.br, sites dos tribunais) se puder buscar; se não puder, deixe marcado `[CONFERIR: ...]` no texto e avise a Aline. Nunca invente número de lei, súmula ou tema repetitivo.
   - **Texto atemporal:** não coloque o ano no título nem no texto ("em 2027", "IPTU 2027") e não fixe valores que mudam todo ano (salário mínimo, teto do INSS, faixas de contribuição, tabelas). Explique a regra e diga onde conferir o valor atualizado (Meu INSS, gov.br, site da Prefeitura). Assim o texto não precisa ser atualizado a cada ano. Anos de leis e súmulas na Base legal podem ficar.
   - **Na prática do escritório:** se `references/observacoes-da-pratica.md` tiver observação da advogada sobre o tema, inclua a seção `## Na prática do escritório` (antes de "Perguntas frequentes"), em primeira pessoa da autora, usando só o que está no arquivo (pode ajustar a redação, nunca o conteúdo). Sem observação sobre o tema, NÃO crie a seção. Jamais invente experiência, casos, números, prazos ou percentuais.
   - **Link para a LP:** não escreva no texto; o blog acrescenta sozinho "Saiba mais: [LP]" quando há LP ativa do tema (`config.json` → `lps`). Quando uma LP nova for ao ar, marque `"ativa": true` nela.
3. **Escreva o artigo** no formato de `references/modelo-artigo.md`.
4. **Escreva a versão curta** para redes (mesmo arquivo de modelo).
5. **Rode o verificador:** `python scripts/checar_texto.py <arquivo.md>`. Ele aponta promessas de resultado, termos proibidos pela OAB, juridiquês e frases longas. Corrija tudo o que for apontado como ERRO; avalie os AVISOS.
6. **Publique no blog** (quando a Aline pedir o post do dia, publique sem perguntar):
   - Copie `assets/blog/` desta skill para `/home/claude/blog-cla/` e rode `pip install markdown --break-system-packages` se faltar.
   - Leia o blog publicado com a ferramenta Artifact (action "read", url em `config.json` → `artifact_url`) e recupere os textos: `python build.py recuperar <caminho do index.html lido>`.
   - Salve o texto novo em `posts/AAAA-MM-DD-slug-curto.md` (slug sem acento, ex.: `2026-10-12-bpc-loas-renda`), exatamente no formato do modelo — o script lê título, resumo, palavras-chave, data, resposta rápida, perguntas frequentes e a área pela linha `Área:` (obrigatória: previdenciário, trabalhista ou tributário).
   - `python build.py spa`, copie `dist/blog.html` para `/mnt/user-data/outputs/blog-cla.html` e publique com Artifact (action "publish", `url` = artifact_url, sem capabilities). Nunca crie um blog novo.
   - Calculadoras: a lista fica em `config.json` (`calc_prev` com nome e link — link vazio aparece como "Em breve"; `calc_trab` com nome e id da aba da LP trabalhista — abre em `lp_trabalhista#calc-<id>`). Para incluir uma calculadora nova ou trocar o link (por exemplo, quando a página previdenciária do escritório ficar pronta), edite essa lista, rode o build e publique.
   - Para levar ao site: `python build.py site` gera `dist/site/` (uma página por texto em /blog/slug/, sitemap.xml, robots.txt liberando os robôs das IAs, llms.txt e feed.xml). Entregue zipado quando pedirem.
   - **Newsletter:** o build também gera a newsletter do dia: um único e-mail com título, autora e resposta rápida de cada texto das três áreas e o link para ler o texto completo no blog (`dist/newsletter/ultima.html`; no site, `/blog/newsletter/ultima.html` + `ultima.json`). O envio é feito pelo script do Google em `assets/blog/google-apps-script/` (Gmail Workspace do escritório, todo dia às 9h); não envie a newsletter pelo conector do Gmail. Quando a Aline passar o endereço `/exec` do script, coloque-o em `config.json` → `form_url`.
7. **Entregue** no chat: confirmação de publicação com o título, a versão curta para redes (para copiar) e pendências (itens `[CONFERIR]`). Não repita o artigo inteiro, ele já está no blog.

## Por que o formato importa (IA e buscadores)

IAs e o Google citam textos que (a) respondem à pergunta logo no primeiro parágrafo, (b) têm perguntas como subtítulos, (c) trazem fonte legal e data, e (d) identificam claramente quem escreveu e onde atua. Por isso o modelo exige: resposta direta no início, subtítulos em forma de pergunta, bloco de perguntas frequentes, data de atualização e assinatura com nome, área e escritório. A cidade (Barueri) ajuda a IA a indicar a advogada certa para quem pergunta "advogado previdenciário em Barueri" ou "advogado trabalhista em Barueri".

## Assinatura (por área) — sem contatos no texto

Cada texto é assinado pela advogada da área, sem número de OAB individual (a OAB da sociedade já está no rodapé da página):

- **Previdenciário:** `**Aline Camargo** — Advogada Previdenciária - Camargo Lourenço Advogados`
- **Trabalhista:** `**Lislie Lourenço** — Advogada Trabalhista - Camargo Lourenço Advogados`
- **Tributário:** `**Aline Camargo** — Advogada Tributária - Camargo Lourenço Advogados`

Na versão curta: `— Aline Camargo, Advogada Previdenciária | Camargo Lourenço Advogados` (troque nome e área conforme o texto).

Texto que mistura duas áreas (ex.: doença ocupacional): assina a advogada do tema principal.

Nos textos, o cargo é sempre o da área do texto (ex.: trabalhista → Advogada Trabalhista; previdenciário → Advogada Previdenciária), mesmo que a advogada atue em outras áreas; o cargo completo fica só na página de equipe. O nome da autora leva à página **/equipe** (dados em `config.json` → `equipe`). Novo advogado que for assinar textos: incluir na equipe, em `AUTORAS` do build e nesta seção.

**Nunca coloque no texto** telefone, WhatsApp, e-mail, site, endereço ou convite para contato ("se quiser que um advogado analise..."). Esses dados ficam no rodapé da página do blog. No artigo e na versão curta, só a assinatura acima.

## Calendário sugerido (quando pedirem a semana)

Seg — previdenciário (benefício/aposentadoria) · Ter — trabalhista (rescisão/verbas) · Qua — tributário (execução fiscal ou isenção de IR) · Qui — previdenciário (incapacidade/BPC/pensão) · Sex — trabalhista (jornada/saúde/acidente) · Sáb — "notícia explicada" ou "mito ou verdade".

## O que não fazer

- Não citar clientes, casos concretos identificáveis, valores obtidos ou "vitórias" do escritório.
- Não falar de honorários, preços, "sem custo", "só paga se ganhar".
- Não criticar colegas, o INSS ou empresas com ataque pessoal; informe o direito.
- Não usar sensacionalismo: "URGENTE", "BOMBA", "o INSS não quer que você saiba".
- Não dar orientação que substitua a análise do caso: sempre deixe claro que cada caso tem detalhes.
