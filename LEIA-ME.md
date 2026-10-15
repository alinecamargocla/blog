# Blog Jurídico CLA — publicação automática com aprovação

## Como funciona todo dia
| Horário (Brasília) | O que acontece |
|---|---|
| 05h | O GitHub publica os textos aprovados que estavam na fila e o Claude (pela API) escreve os 3 textos do cronograma do dia, passa no verificador da OAB e pede aprovação por e-mail. |
| Assim que chega | **Aline** recebe previdenciário e tributário; **Lislie** recebe trabalhista. Cada e-mail traz o texto completo e os botões **Aprovar e publicar**, **Pedir ajuste** e **Não publicar**. |
| Ao aprovar | O texto entra no blog em alguns minutos. Regra: **no máximo um texto por área por dia**. Se a área já teve texto publicado hoje, o aprovado fica na fila e entra no dia seguinte, e assim por diante. |
| Ao pedir ajuste | O Claude reescreve com o comentário e envia a nova versão para aprovação. |
| 12h | Lembrete para quem tem texto aguardando aprovação. Não há prazo: o texto fica pendente até ser decidido. |
| 08h do dia seguinte | Newsletter com a resposta rápida dos textos publicados no dia anterior. |

Textos com pontos **[CONFERIR]** não podem ser aprovados direto: use "Pedir ajuste" e informe o dado correto.
Nada disso depende de computador ligado: roda no GitHub, no Netlify e no Google.

## Instalação (uma vez)
1. **GitHub** — crie uma conta para o escritório e um repositório **privado** chamado `blog`. Envie todos os arquivos desta pasta (botão "Add file → Upload files"), mantendo as pastas.
2. **Anthropic (API do Claude)** — em console.anthropic.com, crie a conta do escritório, cadastre um cartão e gere uma **chave de API**. O custo é por uso; para 3 textos por dia costuma ser baixo (preços em docs.claude.com).
3. **Netlify** — crie a conta do escritório em netlify.com → Add new site → Import an existing project → GitHub → escolha o repositório `blog`. As configurações já estão no arquivo `netlify.toml` (não é preciso alterar nada). Anote o endereço gerado (ex.: `blog-cla.netlify.app`) e passe para a Lumino.
4. **Google (conta contato@)** — crie a planilha **Blog CLA — Newsletter e aprovações** → Extensões → Apps Script → cole `google-apps-script/Codigo.gs`.
   - Em Configurações do projeto → Propriedades do script, crie:
     - `SEGREDO`: uma frase secreta qualquer (a mesma do passo 5);
     - `GITHUB_REPO`: `usuario-do-github/blog`;
     - `GITHUB_TOKEN`: no GitHub, Settings → Developer settings → Fine-grained tokens → acesso só ao repositório `blog`, permissão **Contents: Read and write**.
   - Rode a função **instalar** uma vez e autorize.
   - Implantar → Nova implantação → App da Web → Executar como **Eu** → Acesso **Qualquer pessoa**. Copie o endereço que termina em `/exec`.
5. **Segredos no GitHub** — no repositório: Settings → Secrets and variables → Actions → New repository secret:
   - `ANTHROPIC_API_KEY` (passo 2), `APPS_SCRIPT_URL` (endereço `/exec`), `APPS_SCRIPT_SEGREDO` (a frase do passo 4).
6. **config.json** — confira os e-mails em `aprovadores` e coloque o endereço `/exec` em `form_url` (é o que liga o formulário "Receba por e-mail" à planilha).
7. **Lumino** — envie `ROTEIRO-LUMINO.md` para ligar o endereço `/blog` do site ao Netlify.
8. **Teste** — no GitHub, aba Actions → "Rascunhos do dia e publicação da fila" → Run workflow. Os e-mails de aprovação devem chegar em alguns minutos.

## Manutenção
- **Cronograma**: `cronograma/cronograma.json` (vai até 31/01/2027). Para o próximo período, peça ao Claude um novo cronograma e substitua o arquivo.
- **Regras de escrita**: pasta `skill/` (mesma skill blog-juridico-cla). Ao atualizar a skill, substitua essa pasta.
- **Acompanhamento**: a planilha mostra as abas Aprovações, Inscritos, Dúvidas e Envios. O histórico completo fica em `rascunhos/fila.json`.
