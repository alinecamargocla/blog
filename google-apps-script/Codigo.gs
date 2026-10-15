/**
 * Blog Jurídico — Camargo Lourenço Advogados
 * Script do Google vinculado à planilha "Blog CLA — Newsletter e aprovações", na conta contato@.
 *
 *  1. Formulário do blog (newsletter e dúvidas).
 *  2. Aprovação dos textos: recebe os rascunhos do GitHub, envia o e-mail de aprovação à advogada
 *     responsável e devolve a decisão (aprovar, ajustar, não publicar) ao GitHub.
 *  3. Newsletter: na manhã seguinte, envia a resposta rápida dos textos publicados no dia anterior.
 *
 * Propriedades do script (Configurações do projeto → Propriedades do script):
 *   SEGREDO       = a mesma frase secreta cadastrada no GitHub (APPS_SCRIPT_SEGREDO)
 *   GITHUB_TOKEN  = token do GitHub com permissão de "Contents: write" no repositório do blog
 *   GITHUB_REPO   = dono/repositorio (ex.: camargolourenco/blog)
 * Instalação: LEIA-ME.md. Depois de colar o código, rode "instalar" uma vez.
 */
const CFG = {
  SITE: 'https://www.camargolourenco.adv.br',
  AVISO_DUVIDAS: 'contato@camargolourenco.adv.br',
  RESPONDER_PARA: 'contato@camargolourenco.adv.br',
  REMETENTE: 'Camargo Lourenço Advogados',
  FUSO: 'America/Sao_Paulo',
  HORA_NEWSLETTER: 8,
  HORA_LEMBRETE: 12
};
const AREA = { previdenciario: 'Previdenciário', trabalhista: 'Trabalhista', tributario: 'Tributário' };
const CAB = {
  'Inscritos': ['Data', 'Nome', 'E-mail', 'Status', 'Token', 'Consentimento', 'Origem', 'Cancelado em', 'Última newsletter'],
  'Dúvidas': ['Data', 'Nome', 'E-mail', 'Dúvida', 'Respondida / virou texto?'],
  'Aprovações': ['Recebido em', 'Token', 'Área', 'Pauta de', 'Título', 'Responsável', 'Status', 'Decidido em', 'Comentário', 'Link publicado'],
  'Envios': ['Quando', 'Newsletter de', 'Enviados', 'Pendentes (cota do dia)']
};
const PROP = PropertiesService.getScriptProperties();

function aba_(nome) {
  const pl = SpreadsheetApp.getActiveSpreadsheet();
  let s = pl.getSheetByName(nome);
  if (!s) { s = pl.insertSheet(nome); s.appendRow(CAB[nome]); s.setFrozenRows(1); }
  return s;
}
function linhaPor_(aba, coluna, valor) {
  const d = aba.getDataRange().getValues();
  for (let i = 1; i < d.length; i++) if (String(d[i][coluna - 1]) === String(valor)) return { n: i + 1, v: d[i] };
  return null;
}
function esc_(t) { return String(t || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function pagina_(titulo, corpo) {
  return HtmlService.createHtmlOutput('<div style="font-family:Arial,sans-serif;max-width:560px;margin:40px auto;color:#013366;padding:0 16px">'
    + '<h2 style="font-family:Georgia,serif;font-weight:normal">' + esc_(titulo) + '</h2>' + corpo + '</div>')
    .setTitle(titulo).addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
function hoje_(deslocamento) {
  const d = new Date(); d.setDate(d.getDate() + (deslocamento || 0));
  return Utilities.formatDate(d, CFG.FUSO, 'yyyy-MM-dd');
}

/* ============ Entradas (POST) ============ */
function doPost(e) {
  // 1) Chamadas do GitHub (JSON com segredo)
  if (e.postData && e.postData.type === 'application/json') {
    const d = JSON.parse(e.postData.contents);
    if (d.segredo !== PROP.getProperty('SEGREDO')) return ContentService.createTextOutput('negado');
    if (d.acao === 'rascunho') return rascunhoRecebido_(d);
    if (d.acao === 'publicado') return publicadoAviso_(d);
    if (d.acao === 'bloqueado') return bloqueadoAviso_(d);
    return ContentService.createTextOutput('acao desconhecida');
  }
  const p = e.parameter || {};
  // 2) Confirmação de decisão vinda da página de aprovação
  if (p.acao === 'decidir') return decidir_(p);
  // 3) Formulário do blog
  return formularioBlog_(p);
}

/* ============ Links (GET) ============ */
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.sair) return cancelar_(p.sair);
  if (p.rev) return paginaDecisao_(p.rev, p.d);
  return pagina_('Blog Jurídico', '<p>Página do sistema do blog.</p>');
}

/* ---------- Formulário do blog ---------- */
function formularioBlog_(p) {
  const email = String(p.email || '').trim().toLowerCase();
  const nome = String(p.nome || '').trim().slice(0, 120);
  if (!nome || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || p.consentimento !== 'sim') return ContentService.createTextOutput('erro');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    if (p.receber === 'sim') {
      const s = aba_('Inscritos'); const l = linhaPor_(s, 3, email);
      if (l) { s.getRange(l.n, 4).setValue('Ativo'); s.getRange(l.n, 8).setValue(''); }
      else s.appendRow([new Date(), nome, email, 'Ativo', Utilities.getUuid(), 'Sim — formulário do blog', String(p.origem || '').slice(0, 300), '', '']);
    }
    const duvida = String(p.duvida || '').trim().slice(0, 1500);
    if (duvida) {
      aba_('Dúvidas').appendRow([new Date(), nome, email, duvida, '']);
      MailApp.sendEmail({ to: CFG.AVISO_DUVIDAS, replyTo: email, subject: 'Nova dúvida pelo blog — ' + nome,
        body: 'Nome: ' + nome + '\nE-mail: ' + email + '\n\nDúvida:\n' + duvida });
    }
  } finally { lock.releaseLock(); }
  return ContentService.createTextOutput('ok');
}
function cancelar_(token) {
  const s = aba_('Inscritos'); const l = linhaPor_(s, 5, token);
  if (l) { s.getRange(l.n, 4).setValue('Cancelado'); s.getRange(l.n, 8).setValue(new Date()); }
  return pagina_('Camargo Lourenço Advogados', l ? '<p>Pronto. Você não vai mais receber a newsletter do Blog Jurídico.</p>' : '<p>Link inválido.</p>');
}

/* ---------- Aprovação ---------- */
function rascunhoRecebido_(d) {
  aba_('Aprovações').appendRow([new Date(), d.token, AREA[d.area], d.data_pauta, d.titulo, d.destinatario, 'Aguardando', '', '', '']);
  GmailApp.sendEmail(d.destinatario, d.assunto, 'Abra este e-mail em HTML para ver o texto e os botões de aprovação.',
    { htmlBody: d.html, name: 'Blog Jurídico CLA' });
  return ContentService.createTextOutput('ok');
}
function paginaDecisao_(token, d) {
  const l = linhaPor_(aba_('Aprovações'), 2, token);
  if (!l) return pagina_('Link inválido', '<p>Não encontramos este texto.</p>');
  if (l.v[6] !== 'Aguardando') return pagina_('Já decidido', '<p>Este texto já foi decidido: <b>' + esc_(l.v[6]) + '</b>.</p>');
  const url = ScriptApp.getService().getUrl();
  const rot = { aprovar: 'Aprovar e publicar', ajustar: 'Pedir ajuste', recusar: 'Não publicar' }[d] || 'Aprovar e publicar';
  const caixa = 'width:100%;font:inherit;padding:10px;box-sizing:border-box';
  const campo = d === 'ajustar'
    ? '<p><label for="c"><b>O que precisa mudar?</b></label><br><textarea id="c" name="comentario" rows="6" required style="' + caixa + '"></textarea></p>'
    : d === 'recusar' ? ''
    : '<p><label for="o"><b>Na prática do escritório</b> (opcional)</label><br><small>O que você observa nos casos do escritório sobre este tema, em primeira pessoa. Sem nomes, valores, prazos de casos ou honorários. Entra no texto num quadro próprio.</small><br>'
      + '<textarea id="o" name="observacao" rows="5" style="' + caixa + '"></textarea></p>';
  return pagina_(rot, '<p><b>' + esc_(l.v[2]) + '</b> · ' + esc_(l.v[4]) + '</p>'
    + '<form method="post" action="' + url + '" target="_top">'
    + '<input type="hidden" name="acao" value="decidir"><input type="hidden" name="t" value="' + esc_(token) + '">'
    + '<input type="hidden" name="decisao" value="' + esc_(d || 'aprovar') + '">' + campo
    + '<button style="background:#013366;color:#fff;border:0;padding:12px 22px;border-radius:4px;font-weight:bold;font-size:15px;cursor:pointer">Confirmar: ' + esc_(rot) + '</button></form>');
}
function decidir_(p) {
  const s = aba_('Aprovações'); const l = linhaPor_(s, 2, p.t);
  if (!l || l.v[6] !== 'Aguardando') return pagina_('Já decidido', '<p>Este texto já foi decidido.</p>');
  const decisao = ['aprovar', 'ajustar', 'recusar'].indexOf(p.decisao) >= 0 ? p.decisao : 'aprovar';
  const comentario = String(p.comentario || '').slice(0, 3000);
  const observacao = decisao === 'aprovar' ? String(p.observacao || '').slice(0, 1500) : '';
  const status = { aprovar: 'Aprovado', ajustar: 'Ajuste pedido', recusar: 'Não publicar' }[decisao];
  s.getRange(l.n, 7, 1, 3).setValues([[status, new Date(), comentario || (observacao ? 'Prática: ' + observacao : '')]]);
  UrlFetchApp.fetch('https://api.github.com/repos/' + PROP.getProperty('GITHUB_REPO') + '/dispatches', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: false,
    headers: { Authorization: 'Bearer ' + PROP.getProperty('GITHUB_TOKEN'), Accept: 'application/vnd.github+json' },
    payload: JSON.stringify({ event_type: 'aprovacao', client_payload: { token: p.t, decisao: decisao, comentario: comentario, observacao: observacao, email: l.v[5] } })
  });
  const msg = { aprovar: 'Aprovado. O texto entra no blog em alguns minutos (ou amanhã, se a área já tiver texto publicado hoje).',
    ajustar: 'Ajuste pedido. Você vai receber a nova versão por e-mail em alguns minutos.', recusar: 'Certo, este texto não será publicado.' }[decisao];
  return pagina_(status, '<p>' + esc_(msg) + '</p>');
}
function publicadoAviso_(d) {
  const s = aba_('Aprovações'); const l = linhaPor_(s, 2, d.token);
  if (l) { s.getRange(l.n, 7).setValue('Publicado'); s.getRange(l.n, 10).setValue(d.url); }
  GmailApp.sendEmail(d.destinatario, 'Publicado no blog: ' + d.titulo, 'O texto foi publicado: ' + d.url, { name: 'Blog Jurídico CLA' });
  return ContentService.createTextOutput('ok');
}
function bloqueadoAviso_(d) {
  const s = aba_('Aprovações'); const l = linhaPor_(s, 2, d.token);
  if (l) { s.getRange(l.n, 7).setValue('Aguardando'); s.getRange(l.n, 8).setValue(''); }
  const url = ScriptApp.getService().getUrl() + '?rev=' + encodeURIComponent(d.token) + '&d=ajustar';
  GmailApp.sendEmail(d.destinatario, 'Texto do blog não publicado: há pontos a conferir', d.motivo + '\n\nPedir ajuste: ' + url, { name: 'Blog Jurídico CLA' });
  return ContentService.createTextOutput('ok');
}

/* ---------- Lembrete do meio-dia ---------- */
function lembrete() {
  const d = aba_('Aprovações').getDataRange().getValues().slice(1).filter(r => r[6] === 'Aguardando');
  const porPessoa = {};
  d.forEach(r => (porPessoa[r[5]] = porPessoa[r[5]] || []).push(r));
  const url = ScriptApp.getService().getUrl();
  Object.keys(porPessoa).forEach(email => {
    const itens = porPessoa[email].map(r => '<li><b>' + esc_(r[2]) + '</b>: ' + esc_(r[4]) + ' — <a href="' + url + '?rev=' + r[1] + '&d=aprovar">aprovar</a> · <a href="' + url + '?rev=' + r[1] + '&d=ajustar">pedir ajuste</a></li>').join('');
    GmailApp.sendEmail(email, 'Lembrete: textos do blog aguardando aprovação (' + porPessoa[email].length + ')', 'Há textos aguardando aprovação.',
      { htmlBody: '<div style="font-family:Arial,sans-serif;color:#013366"><p>Estes textos estão aguardando a sua aprovação:</p><ul>' + itens + '</ul><p>O texto completo está no e-mail de aprovação de cada um.</p></div>', name: 'Blog Jurídico CLA' });
  });
}

/* ---------- Newsletter (manhã seguinte) ---------- */
function enviarNewsletter() {
  const ontem = hoje_(-1), semCache = '?t=' + Date.now();
  const r = UrlFetchApp.fetch(CFG.SITE + '/blog/newsletter/' + ontem + '.json' + semCache, { muteHttpExceptions: true });
  if (r.getResponseCode() !== 200) return;             // ontem não houve publicação
  const info = JSON.parse(r.getContentText());
  const html = UrlFetchApp.fetch(CFG.SITE + '/blog/newsletter/' + ontem + '.html' + semCache).getContentText('UTF-8');
  const url = ScriptApp.getService().getUrl();
  const s = aba_('Inscritos'); const dados = s.getDataRange().getValues();
  let enviados = 0, pendentes = 0;
  for (let i = 1; i < dados.length; i++) {
    const r = dados[i];
    if (r[3] !== 'Ativo' || String(r[8]) === info.data) continue;
    if (MailApp.getRemainingDailyQuota() < 2) { pendentes++; continue; }
    const nome = String(r[1]).trim().split(' ')[0] || 'tudo bem';
    const sair = url + '?sair=' + encodeURIComponent(r[4]);
    GmailApp.sendEmail(r[2], info.assunto, 'Olá, ' + nome + '! Os textos estão em ' + CFG.SITE + '/blog/\n\nCancelar a inscrição: ' + sair,
      { htmlBody: html.split('{{NOME}}').join(esc_(nome)).split('{{SAIR}}').join(sair), name: CFG.REMETENTE, replyTo: CFG.RESPONDER_PARA });
    s.getRange(i + 1, 9).setValue(info.data); enviados++;
  }
  aba_('Envios').appendRow([new Date(), info.data, enviados, pendentes]);
}

/* ---------- Instalação ---------- */
function instalar() {
  Object.keys(CAB).forEach(aba_);
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('enviarNewsletter').timeBased().everyDays(1).atHour(CFG.HORA_NEWSLETTER).inTimezone(CFG.FUSO).create();
  ScriptApp.newTrigger('enviarNewsletter').timeBased().everyDays(1).atHour(CFG.HORA_NEWSLETTER + 6).inTimezone(CFG.FUSO).create(); // termina se a cota acabar
  ScriptApp.newTrigger('lembrete').timeBased().everyDays(1).atHour(CFG.HORA_LEMBRETE).inTimezone(CFG.FUSO).create();
}
