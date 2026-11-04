'use strict';
/*
  Stillspace frontend logic.

  Ported from the mentor's mockup (docs/mockup/Stillspace-2.html). The screens,
  layout and behaviour are kept. Every change required by spec section 12 is
  marked with a "CHANGED:" comment so it is easy to compare with the mockup.

  Phase 4 status: strategies, participants, check-ins and chat replies use the
  server. Strategy-aware replies arrive in Phase 7. Look for "STUB (Phase N)".
*/

const $ = id => document.getElementById(id);

// ---------- Settings that come from the server ----------

// CHANGED: strategies were a hard-coded array; now they come from GET /api/config.
let appConfig = null;   // whole /api/config response
let strategies = [];    // just the names, e.g. ['Validation', 'Reflection', ...]

// ---------- Fixed text from the mockup ----------

const names = ['Consent', 'Your check-ins', 'Conversation', 'Reflection', 'Session summary'];
const options = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'];
const phqQuestions = [
  'Little interest or pleasure in doing things',
  'Feeling down, depressed, or hopeless',
  'Trouble falling or staying asleep, or sleeping too much',
  'Feeling tired or having little energy',
  'Poor appetite or overeating',
  'Feeling bad about yourself — or that you are a failure or have let yourself or your family down',
  'Trouble concentrating on things, such as reading the newspaper or watching television',
  'Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual',
  'Thoughts that you would be better off dead, or of hurting yourself'
];
const tones = ['#d9eadb', '#f4e9b8', '#f5d2b4', '#efc7c7'];

// ---------- Participant code (CHANGED: new, spec section 12) ----------

// 3-20 letters or digits; stored upper-case (implementation.md D-09).
const CODE_PATTERN = /^[A-Za-z0-9]{3,20}$/;
const CODE_STORAGE_KEY = 'stillspace_code';

// sessionStorage can throw (private windows, blocked storage), so every access
// is wrapped: the app must still work, it just forgets the code on refresh.
function loadStoredCode() {
  try { return sessionStorage.getItem(CODE_STORAGE_KEY) || ''; } catch (e) { return ''; }
}
function storeCode(code) {
  try { sessionStorage.setItem(CODE_STORAGE_KEY, code); } catch (e) { /* ignore */ }
}
function clearStoredCode() {
  try { sessionStorage.removeItem(CODE_STORAGE_KEY); } catch (e) { /* ignore */ }
}

let participantCode = loadStoredCode();

// CHANGED: the participant's status from the server (what is due, latest PHQ-9,
// saved answers). null means nobody is signed in yet.
let status = null;
let finishing = false;  // stops a double click from saving a check-in twice

// CHANGED: chat state for the server (Phase 4).
let sessionId = null;   // id from POST /api/sessions; a new one for each "New session"
let chatError = null;   // {message, text} after a failed send, shown with a Retry button

// Mood buttons are stored by name so the database is readable (same order as the buttons).
const MOOD_LABELS = ['Low', 'Unsettled', 'Neutral', 'Okay', 'Good'];

// ---------- App state (same variables as the mockup) ----------

let step = 0, unlocked = 0, consent = false, font = 16, preferred = 'Automatic', implemented = null,
    mood = null, tab = 'fortnight', messages = [], phq = {}, extra = {}, daily = {}, setup = {}, post = {},
    busy = false, epoch = 0, started = null, elapsed = 0;
// CHANGED: the mockup's day / setupDone / lastDaily / lastFortnight scheduling
// variables are gone: the server decides what is due (see `status`).

// ---------- Talking to the server (CHANGED: new, spec section 12) ----------

let loadingCount = 0;

// Marks the page busy while any request is running, so screen readers and
// later phases (e.g. disabling buttons) can react to it in one place.
function setLoading(change) {
  loadingCount = Math.max(0, loadingCount + change);
  document.body.setAttribute('aria-busy', loadingCount > 0 ? 'true' : 'false');
}

// Every fetch goes through here: it sends/receives JSON and turns any failure
// into an Error with a friendly message (never a stack trace).
async function api(path, options = {}) {
  const request = { method: options.method || 'GET', headers: {} };
  if (options.body !== undefined) {
    request.headers['Content-Type'] = 'application/json';
    request.body = JSON.stringify(options.body);
  }
  setLoading(+1);
  try {
    let response;
    try {
      response = await fetch(path, request);
    } catch (networkError) {
      throw new Error('Cannot reach the Stillspace server. Please check that it is still running.');
    }
    let data = null;
    try { data = await response.json(); } catch (e) { /* empty or non-JSON body */ }
    if (!response.ok) {
      // FastAPI puts a readable message in "detail"; validation errors use a list, so fall back.
      const detail = data && typeof data.detail === 'string' ? data.detail : null;
      throw new Error(detail || `Something went wrong (error ${response.status}). Please try again.`);
    }
    return data;
  } finally {
    setLoading(-1);
  }
}

// Short message at the bottom of the screen, using the mockup's .toast style.
function notify(text) {
  const box = $('status');
  box.innerHTML = `<div class="toast">${esc(text)}</div>`;
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => { box.innerHTML = ''; }, 5000);
}

// ---------- Small helpers ----------

function esc(s) { const d = document.createElement('div'); d.textContent = String(s); return d.innerHTML; }
function format(ms) { let s = Math.floor(ms / 1000); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }

// CHANGED: description of a strategy from /api/config, shown as a tooltip.
function describe(name) {
  const found = appConfig ? appConfig.strategies.find(s => s.name === name) : null;
  return found ? found.description : '';
}
function strategyOptions(selected) {
  return strategies.map(s => `<option ${selected === s ? 'selected' : ''} title="${esc(describe(s))}">${esc(s)}</option>`).join('');
}

// ---------- Navigation ----------

function go(n) {
  if (n > unlocked) return;
  if (step === 2 && n !== 2 && started) { elapsed += Date.now() - started; started = null; }
  if (n === 2 && !started) started = Date.now();
  step = n;
  render();
  $('shell').classList.remove('menu');
  window.scrollTo(0, 0);
}
function advance() { unlocked = Math.max(unlocked, step + 1); go(step + 1); }
function enterChat() { unlocked = Math.max(unlocked, 2); go(2); }

// CHANGED: shows who is signed in, with a "Switch participant" link (spec section 12).
function renderParticipantBox() {
  const box = $('participantbox');
  box.hidden = !status;  // hidden, not just empty, so the sidebar spacing matches the mockup
  if (!status) { box.innerHTML = ''; return; }
  box.innerHTML = `<p class="tiny" style="margin:0 12px">Signed in as ${esc(status.code)}<br><button type="button" class="textbutton" id="switchParticipant">Switch participant</button></p>`;
  $('switchParticipant').onclick = switchParticipant;
}

function nav() {
  renderParticipantBox();
  $('nav').innerHTML = names.map((n, i) => `<button class="${i === step ? 'active' : ''}" ${i > unlocked ? 'disabled' : ''} data-step="${i}" ${i === step ? 'aria-current="step"' : ''}><span class="stepnum">${i < step ? '✓' : i + 1}</span>${n}</button>`).join('');
  document.querySelectorAll('[data-step]').forEach(b => b.onclick = () => go(+b.dataset.step));
  $('pagetitle').textContent = names[step];
}

// ---------- Right rail: risk, mood, strategies ----------

// CHANGED: also "Follow-up needed" when the latest saved PHQ-9 had item 9 > 0 (spec 11.5).
// Phase 5 adds safety replies in this session to the same rule.
function followUpNeeded() {
  return phq[8] > 0 || Boolean(status && status.latest_phq && status.latest_phq.item9_flag);
}

function risk() {
  const flag = followUpNeeded();
  return `<div class="riskbox"><div class="row" style="justify-content:space-between"><strong>Risk indicator</strong><span class="tag">Prototype</span></div><div class="gradient">${flag ? '<i class="marker" style="--position:92%"></i>' : ''}</div><div class="ends"><span>Lower concern</span><span>Higher concern</span></div><div class="riskstatus">${flag ? 'Follow-up needed' : 'Not assessed'}</div><p class="tiny">${flag ? 'A response to PHQ-9 item 9 needs a human follow-up. This is not a calculated risk level.' : 'No validated safety assessment is connected. Mood, stress and a low PHQ-9 score cannot establish safety.'}</p><div class="tiny">PHQ-9: ${Object.keys(phq).length}/9 answered · chat assessment not connected</div></div>`;
}

// CHANGED: the select id is a parameter (the mockup used string replacement
// for the mobile copy); options come from /api/config; wording made accurate.
function support(selectId = 'preferred') {
  return `<h3>Support strategies</h3><label class="labelblock" for="${selectId}">Requested by you</label><select class="field" id="${selectId}"><option>Automatic</option>${strategyOptions(preferred)}</select><p class="tiny">Change this any time. Your request is a preference, separate from the style used.</p><div class="labelblock">Currently used by model</div><output class="strategyused">${implemented || 'Awaiting first reply'}</output><p class="tiny">Read-only · chosen for each reply, so it can differ from your request.</p>`;
}

function moodHtml() {
  return `<h3>How are you feeling today?</h3><div class="moods">${[['😟', 'Low'], ['🙁', 'Unsettled'], ['😐', 'Neutral'], ['🙂', 'Okay'], ['😊', 'Good']].map(([e, n], i) => `<button style="--tone:${['#efc7c7', '#f5d2b4', '#f4e9b8', '#e5edc7', '#d9eadb'][i]}" aria-label="${n}" aria-pressed="${mood === i}" class="${mood === i ? 'selected' : ''}" data-mood="${i}">${e}<small>${n}</small></button>`).join('')}</div><p class="tiny">${mood === null ? 'Optional · choose what feels closest.' : 'Mood selected for today. You can change it.'}</p>`;
}

function renderContext() {
  // CHANGED: "About this demo" -> "About Stillspace".
  $('rail').innerHTML = risk() + `<section>${moodHtml()}</section><section>${support()}</section><section><h3>Session at a glance</h3><div class="row" style="justify-content:space-between"><span class="sub">Chat time</span><strong data-clock>${format(elapsed + (started ? Date.now() - started : 0))}</strong></div><div class="row" style="justify-content:space-between"><span class="sub">Messages sent</span><strong>${messages.filter(m => m.role === 'user').length}</strong></div></section><button data-help style="width:100%">About Stillspace ↗</button>`;
  const mobileBox = $('mobilecontext');
  if (mobileBox) mobileBox.innerHTML = `<summary>Risk: ${followUpNeeded() ? 'follow-up needed' : 'not assessed'} · Support & mood ▾</summary><div class="contextbody">${risk()}${moodHtml()}${support('mobilepreferred')}</div>`;
  bindContext();
}

function bindContext() {
  document.querySelectorAll('[data-mood]').forEach(b => b.onclick = () => {
    mood = +b.dataset.mood;
    renderContext();
    if (step === 1 && tab === 'daily') survey();
    saveMood();  // CHANGED: the sidebar and daily mood write the same daily check-in
  });
  ['preferred', 'mobilepreferred', 'setupstyle'].forEach(id => {
    const e = $(id);
    if (e) {
      e.value = preferred;
      e.onchange = () => {
        preferred = e.value;
        setup.preferred = preferred;
        renderContext();
        if ($('setupstyle')) $('setupstyle').value = preferred;
        savePreference();  // CHANGED: "Requested by you" is saved (PATCH)
      };
    }
  });
  document.querySelectorAll('[data-help]').forEach(b => b.onclick = () => $('help').showModal());
}

function render() {
  nav();
  if (step === 0) welcome();
  if (step === 1) survey();
  if (step === 2) chat();
  if (step === 3) reflection();
  if (step === 4) summary();
  renderContext();
}

function mobile() { return '<details class="mobilecontext" id="mobilecontext"></details>'; }

// ---------- Step 0: welcome and consent ----------

// CHANGED: participant code field added; wording made accurate (spec section 12).
function welcome() {
  $('view').innerHTML = `<div class="intro"><div class="eyebrow">Welcome · take your time</div><h1>A space to talk.<br>A moment to breathe.</h1><p class="sub">Explore different styles of support, with space to check in and reflect.</p><div class="journey"><article><span class="symbol">☷</span><strong>Your check-ins</strong><p>Optional questions, at your pace.</p></article><article><span class="symbol">◌</span><strong>Your conversation</strong><p>A place to share what is on your mind.</p></article><article><span class="symbol">❧</span><strong>Your reflection</strong><p>A small moment to look back.</p></article></div><div class="card"><strong>Before we begin</strong><p class="sub">This is a student research prototype. Your answers and messages are saved on this computer for the research project, linked to your participant code. ${appConfig && appConfig.mock_mode ? 'Replies are mock replies for now, not from an AI model.' : 'Replies are generated by an AI model.'} PHQ-9 answers give a screening score; they are not a diagnosis or a safety assessment. This is not therapy or an emergency service.</p><label class="labelblock" for="pcode">Participant code</label><input class="field" id="pcode" autocomplete="off" spellcheck="false" maxlength="20" placeholder="e.g. P001" value="${esc(participantCode)}" aria-describedby="pcodehint"><label class="check"><input type="checkbox" id="agree" ${consent ? 'checked' : ''}><span>I understand this is a research prototype, not therapy or an emergency service, and I agree to take part.</span></label><p class="tiny codehint" id="pcodehint" aria-live="polite"></p><div class="row"><button class="primary" id="begin">Continue →</button><button id="direct">Skip to chat →</button></div><p class="tiny">You can skip any question. Chat is not an emergency service.</p></div></div>`;
  $('agree').onchange = e => { consent = e.target.checked; updateConsentButtons(); };
  $('pcode').oninput = updateConsentButtons;
  $('begin').onclick = () => login('route');
  $('direct').onclick = () => login('chat');
  updateConsentButtons();
}

// Both buttons stay disabled until the box is ticked AND the code is valid,
// and the hint line says exactly what is still missing.
function updateConsentButtons() {
  const code = $('pcode').value.trim();
  const codeOk = CODE_PATTERN.test(code);
  let hint = '';
  if (!code) hint = 'Enter the participant code you were given (3–20 letters or digits).';
  else if (!codeOk) hint = 'The participant code can only use letters and digits, 3–20 characters, no spaces.';
  else if (!consent) hint = 'Tick the box above to continue.';
  const hintBox = $('pcodehint');
  hintBox.textContent = hint;
  hintBox.classList.toggle('invalid', Boolean(code) && !codeOk);
  $('begin').disabled = $('direct').disabled = !(consent && codeOk);
}

// CHANGED: sign in with POST /api/participants (creates the code if new), keep
// the code for this tab, then go to whatever is due (spec section 12).
async function login(target) {
  const code = $('pcode').value.trim();
  if (!consent || !CODE_PATTERN.test(code)) { updateConsentButtons(); return; }
  $('begin').disabled = $('direct').disabled = true;
  try {
    const result = await api('/api/participants', { method: 'POST', body: { code } });
    participantCode = result.status.code;
    storeCode(participantCode);
    applyStatus(result.status);
    if (target === 'chat') enterChat(); else routeByStatus();
  } catch (error) {
    notify(error.message);
    updateConsentButtons();
  }
}

// ---------- Server status and saving (CHANGED: new, spec section 12) ----------

// Copy what the server knows into the page: preference, today's mood and the
// saved answers. Used after sign-in, refresh and the demo day buttons.
function applyStatus(newStatus) {
  status = newStatus;
  preferred = newStatus.preferred_strategy;
  const moodIndex = MOOD_LABELS.indexOf(newStatus.today_mood);
  mood = moodIndex >= 0 ? moodIndex : null;
  daily = { ...newStatus.answers.daily };
  delete daily.mood;  // mood has its own variable, like in the mockup
  const fortnight = newStatus.answers.fortnightly || {};
  phq = { ...(fortnight.phq || {}) };
  extra = { ...(fortnight.extra || {}) };
  setup = { ...newStatus.answers.setup };
}

// Order from spec section 12: setup, then daily, then the two-week check-in.
function nextDueTab() {
  if (!status) return null;
  if (!status.setup_done) return 'setup';
  if (status.daily_due) return 'daily';
  if (status.fortnightly_due) return 'fortnight';
  return null;
}

function routeByStatus() {
  const dueTab = nextDueTab();
  if (dueTab) { tab = dueTab; unlocked = Math.max(unlocked, 1); go(1); }
  else enterChat();
}

function goToNextDue() {
  const dueTab = nextDueTab();
  if (dueTab) { tab = dueTab; survey(); window.scrollTo(0, 0); }
  else enterChat();
}

// Sends one check-in. Only the server's answer updates `status`, so the
// Due/Done labels always show what is really stored.
async function saveCheckin(type, answers) {
  try {
    const result = await api('/api/checkins', { method: 'POST', body: { code: participantCode, type, answers } });
    status = result.status;
    return result;
  } catch (error) {
    notify(error.message);
    return null;
  }
}

// Wraps the three "Finish/Save" buttons so a double click saves only once.
async function finishCheckin(type, answers) {
  if (finishing) return null;
  finishing = true;
  try { return await saveCheckin(type, answers); } finally { finishing = false; }
}

async function saveSetupAnswers() {
  const result = await finishCheckin('setup', { dob: setup.dob, preferred: setup.preferred });
  if (result) { preferred = status.preferred_strategy; goToNextDue(); }
}

async function saveDailyAnswers() {
  // null tells the server to remove an answer that was skipped after being saved.
  const answers = { ...daily, dailySupport: daily.dailySupport ?? null, mood: mood === null ? null : MOOD_LABELS[mood] };
  if (await finishCheckin('daily', answers)) goToNextDue();
}

async function saveFortnightlyAnswers() {
  const result = await finishCheckin('fortnightly', { phq, extra });
  if (!result) return;
  const c = result.checkin;
  notify(c.phq_complete ? `Saved. PHQ-9 total ${c.phq_total} (${c.phq_band}).` : 'Saved. The PHQ-9 is incomplete, so no total is stored.');
  goToNextDue();
}

// Mood buttons save immediately (upsert of today's daily check-in).
async function saveMood() {
  if (!status) return;  // not signed in yet: nothing to save to
  const result = await saveCheckin('daily', { mood: mood === null ? null : MOOD_LABELS[mood] });
  if (result && step === 1) survey();  // refresh the Due/Done labels
}

async function savePreference() {
  if (!status) return;
  try {
    status = await api(`/api/participants/${encodeURIComponent(participantCode)}`, { method: 'PATCH', body: { preferred_strategy: preferred } });
  } catch (error) {
    notify(error.message);
  }
}

// Demo buttons: move this participant's demo date on the server, then reload status.
async function previewVisit(days) {
  try {
    applyStatus(await api('/api/demo/advance', { method: 'POST', body: { code: participantCode, days } }));
    tab = status.fortnightly_due ? 'fortnight' : 'daily';  // same choice as the mockup
    unlocked = Math.max(unlocked, 1);
    go(1);
  } catch (error) {
    notify(error.message);
  }
}

// ---------- Step 1: check-ins ----------

function score() {
  const count = Object.keys(phq).length;
  const total = Object.values(phq).reduce((a, b) => a + b, 0);
  const complete = count === 9;
  const band = total < 5 ? 'Minimal' : total < 10 ? 'Mild' : total < 15 ? 'Moderate' : total < 20 ? 'Moderately severe' : 'Severe';
  return `<div class="scorebox"><div class="row" style="justify-content:space-between"><div><div class="eyebrow">Depression score · PHQ-9</div><strong>${complete ? total + ' / 27' : count ? total + ' so far' : '— / 27'}</strong></div><span class="tag">${count}/9 answered</span></div><div class="gradient">${count ? `<i class="marker" style="--position:${Math.max(1, Math.min(99, total / 27 * 100))}%"></i>` : ''}</div><div class="ends"><span>0 · Minimal</span><span>27 · Severe</span></div><p class="sub">${complete ? band + ' symptom range · screening result, not a diagnosis.' : 'Incomplete · no severity result. Unanswered questions are not scored as zero.'}</p></div>`;
}

// CHANGED: "This demo cannot assess..." -> "This app cannot assess..." (it is no longer just a demo).
function alertHtml() {
  return phq[8] > 0 ? `<div class="followup" role="status"><strong>A human follow-up matters here.</strong><p>Thank you for answering. This app cannot assess your immediate safety or contact anyone. If this reflects how you feel, consider reaching out to a trusted person or qualified mental health professional. If you may act on these thoughts now, contact local emergency services.</p><p class="tiny">This notice is triggered by item 9 independently of the total score. You can continue or skip to the chat.</p></div>` : '';
}

function questionHeader(q) { return `<legend>${esc(q)}</legend>`; }
function skipButton(group, key) { return `<button type="button" class="textbutton" data-skipgroup="${group}" data-skipkey="${key}">Skip for now</button>`; }

function phqHtml() {
  return `<div id="score">${score()}</div><div class="card"><div class="eyebrow">Every two weeks · 9 questions</div><h2 style="font-size:1.65rem">A check-in over time</h2><p class="sub">Over the last 2 weeks, how often have you been bothered by any of the following problems?</p>${phqQuestions.map((q, i) => `<fieldset class="phqrow">${questionHeader((i + 1) + '. ' + q)}<div class="responsegrid">${options.map((o, v) => `<label><input type="radio" name="phq${i}" data-group="phq" data-key="${i}" value="${v}" ${phq[i] === v ? 'checked' : ''}><span style="--tone:${tones[v]}"><b>${v}</b>${o}</span></label>`).join('')}</div>${skipButton('phq', i)}</fieldset>`).join('')}<div id="followup">${alertHtml()}</div><p class="tiny">PHQ-9 · Developed by Drs. Robert L. Spitzer, Janet B. W. Williams, Kurt Kroenke and colleagues. <a href="https://med.stanford.edu/fastlab/research/imapp/_jcr_content/main/accordion_copy/accordion_content3/download_256324296/file.res/PHQ9%20id%20date%2008.03.pdf" target="_blank" rel="noopener">Original questionnaire ↗</a></p></div><div class="card"><div class="eyebrow">After the nine questions</div><h2 style="font-size:1.65rem">A little more context</h2><fieldset class="phqrow">${questionHeader('How difficult have these problems made work, home life or getting along with others?')}<div class="choices" style="flex-wrap:wrap">${['Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult'].map(v => `<label><input type="radio" name="difficulty" data-group="extra" data-key="difficulty" value="${v}" ${extra.difficulty === v ? 'checked' : ''}><span>${v}</span></label>`).join('')}</div><p class="tiny">PHQ-9 functional impact follow-up · not included in the 0–27 score.</p>${skipButton('extra', 'difficulty')}</fieldset>${scaleQuestion('wellbeing', 'How would you rate your overall mental well-being currently?', 'Very poor', 'Very good', true, extra)}${scaleQuestion('stress', 'How would you rate your stress levels on average?', 'No stress', 'Extremely high stress', false, extra)}${yesNo('support', 'Do you feel supported by your family and friends regarding your mental health?', 'extra', extra)}<p class="tiny">Additional well-being questions are separate from PHQ-9 scoring. Scale adapted to 0–10 for this prototype. <a target="_blank" rel="noopener" href="https://www.zonkafeedback.com/blog/mental-health-survey-questions">Question reference ↗</a></p></div>`;
}

function tone(v, reverse) { const idx = Math.round((reverse ? 10 - v : v) / 10 * 3); return tones[idx]; }

function scaleQuestion(key, q, left, right, reverse, data, group = 'extra') {
  return `<fieldset class="phqrow">${questionHeader(q)}<div class="numberline" role="group" aria-label="${esc(q)}">${Array.from({ length: 11 }, (_, v) => `<label><input type="radio" name="${key}" value="${v}" data-group="${group}" data-key="${key}" ${data[key] === v ? 'checked' : ''}><span style="--tone:${tone(v, reverse)}">${v}</span></label>`).join('')}</div><div class="gradient ${reverse ? 'reverse' : ''}">${data[key] !== undefined ? `<i class="marker" style="--position:${Math.max(1, Math.min(99, data[key] * 10))}%"></i>` : ''}</div><div class="ends"><span>0 · ${left}</span><span>10 · ${right}</span></div><p class="tiny" data-selection="${key}">${data[key] !== undefined ? 'Selected: ' + data[key] + ' / 10' : 'No answer selected'}</p>${skipButton(group, key)}</fieldset>`;
}

function yesNo(key, q, group, data) {
  return `<fieldset class="phqrow">${questionHeader(q)}<div class="choices">${['Yes', 'No', 'Not sure'].map(v => `<label><input type="radio" name="${group + key}" data-group="${group}" data-key="${key}" value="${v}" ${data[key] === v ? 'checked' : ''}><span>${v}</span></label>`).join('')}</div>${skipButton(group, key)}</fieldset>`;
}

// CHANGED: strategy list from /api/config; wording no longer says "demo" / "only in this open page".
function setupHtml() {
  return `<div class="card"><span class="tag">Once at setup</span><h2 style="font-size:1.65rem">Make this space yours.</h2><p class="sub">These questions are asked once. Your preferred support style remains editable later.</p><label class="labelblock" for="dob">Date of birth · optional</label><input class="field" id="dob" type="date" max="${new Date().toISOString().slice(0, 10)}" value="${setup.dob || ''}">${skipButton('setup', 'dob')}<label class="labelblock" for="setupstyle">What support style would you prefer?</label><select class="field" id="setupstyle"><option>Automatic</option>${strategyOptions(preferred)}</select><p class="tiny">${strategies.map(esc).join(' · ')}. Automatic means no specific request.</p>${skipButton('setup', 'preferred')}<div class="actions"><button class="primary" id="completeSetup">Save setup →</button></div><p class="tiny">Setup is saved with your participant code on this computer.</p></div>`;
}

function dailyHtml() {
  return `<div class="card"><span class="tag">Daily / at login</span><h2 style="font-size:1.65rem">How is today feeling?</h2><p class="sub">A short check-in. The sidebar mood control updates the same answer.</p><div id="dailymoods">${moodHtml()}</div><button class="textbutton" id="skipMood">Skip for now</button>${yesNo('dailySupport', 'Would you like some support today?', 'daily', daily)}<p class="tiny">Sample daily question · replace with your final wording.</p><div class="actions"><button class="primary" id="completeDaily">Finish daily check-in →</button></div></div>`;
}

// CHANGED: Due/Done comes from the server's status; "Scheduling is simulated
// in this open page" and "in this demo" removed; the preview-day label only
// shows in demo mode; every Finish/Save button stores the check-in.
function survey() {
  const pendingSetup = !status || !status.setup_done;
  const pendingDaily = !status || status.daily_due;
  const pendingFortnight = !status || status.fortnightly_due;
  const dayLabel = appConfig && appConfig.demo_mode && status ? ` · preview day ${status.demo_day_offset + 1} (${status.local_date})` : '';
  $('view').innerHTML = mobile() + `<div class="survey"><div class="surveybar"><div><strong>Your check-ins</strong><div class="sub">All optional${dayLabel}</div></div><button class="primary" id="skipChat">Skip to chat →</button></div><div class="tabs" role="tablist" aria-label="Check-in frequency">${[['fortnight', 'Every two weeks', pendingFortnight], ['daily', 'Daily / at login', pendingDaily], ['setup', 'Once at setup', pendingSetup]].map(([id, t, due]) => `<button role="tab" id="tab-${id}" aria-selected="${tab === id}" aria-controls="surveycontent" data-tab="${id}">${t} <span class="tiny">${due ? '· Due' : '· Done'}</span></button>`).join('')}</div><p class="tiny">Due and Done follow your previous check-ins. Skips remain unanswered; completion is an explicit action.</p><div id="surveycontent" role="tabpanel" aria-labelledby="tab-${tab}">${tab === 'fortnight' ? phqHtml() : tab === 'daily' ? dailyHtml() : setupHtml()}</div><div class="actions"><button id="surveyBack">← Back</button><button class="primary" id="surveyNext">${tab === 'fortnight' ? 'Finish two-week check-in →' : tab === 'daily' ? 'Finish daily check-in →' : 'Save setup →'}</button></div><p class="tiny">Finishing with skipped items leaves the PHQ-9 incomplete. Skipped questions can be revisited at any time.</p></div>`;
  $('skipChat').onclick = enterChat;
  $('surveyBack').onclick = () => go(0);
  document.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => { tab = b.dataset.tab; survey(); });
  $('surveyNext').onclick = () => {
    if (tab === 'fortnight') saveFortnightlyAnswers();
    else if (tab === 'daily') saveDailyAnswers();
    else saveSetupAnswers();
  };
  if ($('dob')) $('dob').oninput = e => setup.dob = e.target.value;
  if ($('completeSetup')) $('completeSetup').onclick = saveSetupAnswers;
  if ($('completeDaily')) $('completeDaily').onclick = saveDailyAnswers;
  if ($('skipMood')) $('skipMood').onclick = () => {
    const wasSaved = status && status.today_mood;
    mood = null;
    survey();
    if (wasSaved) saveMood();  // remove the stored mood too
  };
  bindAnswers();
  renderContext();
}

function bindAnswers() {
  const groups = { phq, extra, daily, setup, post };
  document.querySelectorAll('input[data-group]').forEach(e => e.onchange = () => {
    groups[e.dataset.group][e.dataset.key] = e.dataset.group === 'phq' || e.closest('.numberline') ? +e.value : e.value;
    if (e.dataset.group === 'phq') {
      $('score').innerHTML = score();
      $('followup').innerHTML = alertHtml();
      renderContext();
    } else if (e.closest('.numberline')) {
      const field = e.closest('fieldset');
      field.querySelector('[data-selection]').textContent = 'Selected: ' + e.value + ' / 10';
      field.querySelector('.gradient').innerHTML = `<i class="marker" style="--position:${Math.max(1, Math.min(99, +e.value * 10))}%"></i>`;
    }
  });
  document.querySelectorAll('[data-skipgroup]').forEach(b => b.onclick = () => {
    const g = b.dataset.skipgroup, k = b.dataset.skipkey;
    delete groups[g][k];
    if (g === 'setup' && k === 'preferred') preferred = 'Automatic';
    if (step === 1) {
      survey();
      const match = document.querySelector(`[data-skipgroup="${g}"][data-skipkey="${k}"]`);
      if (match) { match.focus(); match.textContent = 'Skipped · optional'; }
    } else reflection();
  });
}

// ---------- Step 2: conversation ----------

// CHANGED: the mockup's demo status line replaced by an accurate one (mock or AI).
function chat() {
  const modeLine = appConfig && appConfig.mock_mode ? 'Mock mode · replies are not from an AI model' : 'Replies are generated by an AI model';
  $('view').innerHTML = mobile() + `<div class="chat"><div class="chathead"><div><strong>Your conversation</strong><div class="tiny"><span class="dot"></span>${modeLine}</div></div><div class="row"><button class="chatreturn" id="returnSurvey">Check-ins</button><button id="finish">Finish & reflect →</button></div></div><div class="messages" id="messages" role="log" aria-live="polite" aria-label="Conversation"></div><div id="chips" class="promptchips"><button>I've had a busy day</button><button>I want to sort through a feeling</button><button>I could use encouragement</button></div><form class="composer" id="form"><label class="tiny" for="input">Your message</label><textarea id="input" placeholder="What’s on your mind?" maxlength="3000"></textarea><div class="composerfooter"><span class="tiny">Use the side panel to change your requested style.</span><button class="primary" id="send" type="submit" aria-label="Send message" disabled>↑ Send</button></div></form><div class="tiny" style="text-align:center;margin-top:9px">Enter to send · Shift + Enter for a new line · Not personalised advice.</div></div>`;
  drawMessages();
  $('input').oninput = () => { $('send').disabled = !$('input').value.trim() || busy; };
  $('form').onsubmit = e => { e.preventDefault(); send(); };
  $('input').onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } };
  document.querySelectorAll('#chips button').forEach(b => b.onclick = () => { $('input').value = b.textContent; send(); });
  $('finish').onclick = advance;
  $('returnSurvey').onclick = () => go(1);
  ensureSession().catch(error => notify(error.message));  // CHANGED: one server session per chat
}

// CHANGED: create the chat session the first time the chat is opened (spec section 12).
async function ensureSession() {
  if (sessionId || !status) return sessionId;
  const result = await api('/api/sessions', { method: 'POST', body: { code: participantCode } });
  sessionId = result.session_id;
  return sessionId;
}

// Badge text for a reply: the strategy once Phase 7 adds it, otherwise where the reply came from.
function replyBadge(m) {
  if (m.strategy) return m.strategy;
  return { mock: 'Mock reply', fallback: 'Fallback reply' }[m.source] || 'AI reply';
}

// CHANGED: badges no longer say "Sample welcome" / "... example".
function drawMessages() {
  if (!$('messages')) return;
  $('messages').innerHTML = `<div class="message"><div class="author">∿ Stillspace <span class="strategybadge">Welcome</span></div><p>Welcome. You can start wherever feels comfortable. Would you like to talk something through, feel heard, or explore a small next step?</p></div>` + messages.map(m => `<div class="message ${m.role}">${m.role === 'assistant' ? `<div class="author">∿ Stillspace <span class="strategybadge">${esc(replyBadge(m))}</span></div>` : ''}<p style="white-space:pre-wrap">${esc(m.text)}</p></div>`).join('') + (busy ? '<p class="tiny" role="status">Stillspace is typing…</p>' : '')
    + (chatError && !busy ? `<div class="chaterror" role="alert"><span>${esc(chatError.message)}</span><button type="button" id="retrySend">Retry</button></div>` : '');
  if ($('retrySend')) $('retrySend').onclick = retrySend;
  $('messages').scrollTop = $('messages').scrollHeight;
  if ($('chips')) $('chips').style.display = messages.length ? 'none' : 'flex';
}

// CHANGED: replies come from POST /api/chat (spec section 12): typing
// indicator while waiting, send disabled, friendly error with Retry on failure.
function send() {
  const text = $('input').value.trim();
  if (!text || busy) return;
  messages.push({ role: 'user', text, requestedStrategy: preferred });
  $('input').value = '';
  requestReply(text);
}

// Retry re-sends the same text; the user message is already on screen.
function retrySend() {
  if (chatError && !busy) requestReply(chatError.text);
}

async function requestReply(text) {
  busy = true;
  chatError = null;
  if ($('send')) $('send').disabled = true;
  drawMessages();
  renderContext();
  const token = epoch;  // if "New session" is pressed meanwhile, ignore this answer
  try {
    await ensureSession();
    const result = await api('/api/chat', { method: 'POST', body: { session_id: sessionId, message: text, requested_strategy: preferred } });
    if (token !== epoch) return;
    if (result.used_strategy) implemented = result.used_strategy;
    messages.push({ role: 'assistant', text: result.reply, strategy: result.used_strategy, source: result.source });
  } catch (error) {
    if (token !== epoch) return;
    chatError = { message: error.message, text };
  } finally {
    if (token === epoch) {
      busy = false;
      drawMessages();
      if ($('send')) $('send').disabled = !$('input').value.trim();
      renderContext();
    }
  }
}

// ---------- Step 3: reflection ----------

function reflection() {
  $('view').innerHTML = mobile() + `<div class="survey"><div class="surveybar"><strong>Your reflection · optional</strong><button id="skipReflection">Skip for now →</button></div><h2>How did that feel?</h2><p class="sub">Sample post-session questions, ready for your final study wording.</p><div class="card">${scaleQuestion('comfort', 'How comfortable did you feel sharing your thoughts?', 'Not at all', 'Very comfortable', true, post, 'post')}${scaleQuestion('validation', 'How understood or validated did you feel?', 'Not at all', 'Very much', true, post, 'post')}${yesNo('useful', 'Did you find this conversation helpful?', 'post', post)}<div class="actions"><button id="backChat">← Back to chat</button><button class="primary" id="viewSummary">View summary →</button></div></div></div>`;
  bindAnswers();
  $('backChat').onclick = () => go(2);
  $('viewSummary').onclick = $('skipReflection').onclick = advance;
  renderContext();
}

// ---------- Step 4: summary ----------

// CHANGED: strategy bars from /api/config; preview-day card only in demo mode;
// wording no longer says "model example" or "does not save personal data".
function summary() {
  const count = messages.filter(m => m.role === 'user').length;
  const previewCard = appConfig && appConfig.demo_mode ? `<div class="card"><h3>Preview repeat visits</h3><p class="sub">Demo mode: try the check-in schedules without waiting. This moves the demo date forward; it does not schedule reminders.</p><div class="daycontrols"><button data-visit="0">Same-day login</button><button data-visit="1">Next day</button><button data-visit="14">14 days later</button></div></div>` : '';
  $('view').innerHTML = mobile() + `<div class="survey"><div class="eyebrow">Session complete</div><h2>Thank you for taking a moment.</h2><p class="sub">A snapshot of your session.</p><div class="split" style="margin-top:28px"><div class="metric"><span class="sub">Conversation time</span><strong>${format(elapsed)}</strong></div><div class="metric"><span class="sub">Messages sent</span><strong>${count}</strong></div></div>${score()}<div class="card"><h3>Support styles explored</h3>${strategies.map(s => { const n = messages.filter(m => m.strategy === s).length; return `<div class="row" style="justify-content:space-between"><span class="sub">${esc(s)}</span><span class="tiny">${n} ${n === 1 ? 'reply' : 'replies'}</span></div><div class="bar"><div style="width:${count ? n / count * 100 : 0}%"></div></div>`; }).join('')}<p class="tiny">Requested style: ${esc(preferred)}. Last style used by the model: ${esc(implemented || 'No reply yet')}. These are separate values.</p></div>${previewCard}<div class="actions"><button id="review">← Review reflection</button><button id="restart" class="primary">Start new session</button></div></div>`;
  $('review').onclick = () => go(3);
  $('restart').onclick = reset;
  document.querySelectorAll('[data-visit]').forEach(b => b.onclick = () => previewVisit(+b.dataset.visit));
  renderContext();
}

// CHANGED: "New session" keeps the participant and their check-in history,
// clears the conversation and starts a new server session (spec section 12).
function reset() {
  if (!status) { switchParticipant(); return; }
  if (messages.length && !confirm('Start a new session? Your check-ins stay saved; this conversation will be cleared from the screen.')) return;
  epoch++;
  messages = []; post = {}; implemented = null; busy = false; started = null; elapsed = 0;
  sessionId = null; chatError = null;  // the next chat creates a fresh server session
  enterChat();
}

// CHANGED: forget the code in this tab and go back to the consent page.
function switchParticipant() {
  clearStoredCode();
  participantCode = ''; status = null; sessionId = null; chatError = null;
  epoch++;
  step = unlocked = 0; consent = false; mood = null; preferred = 'Automatic'; implemented = null; tab = 'fortnight';
  messages = []; phq = {}; extra = {}; daily = {}; setup = {}; post = {}; busy = false;
  started = null; elapsed = 0;
  render();
}

// ---------- Start-up ----------

// Buttons in the static page (theme, text size, menu, help) work even before
// the server answers, exactly as in the mockup.
$('closeHelp').onclick = () => $('help').close();
$('theme').onclick = () => document.body.classList.toggle('dark');
$('larger').onclick = () => { font = Math.min(20, font + 1); document.documentElement.style.fontSize = font + 'px'; };
$('smaller').onclick = () => { font = Math.max(14, font - 1); document.documentElement.style.fontSize = font + 'px'; };
$('newSession').onclick = reset;
$('menu').onclick = () => $('shell').classList.toggle('menu');
setInterval(() => document.querySelectorAll('[data-clock]').forEach(e => e.textContent = format(elapsed + (started ? Date.now() - started : 0))), 1000);

// CHANGED: load settings first, then draw the page. If the server cannot be
// reached, show a friendly message instead of a broken page.
async function start() {
  try {
    appConfig = await api('/api/config');
    strategies = appConfig.strategies.map(s => s.name);
    $('mocktag').hidden = !appConfig.mock_mode;  // CHANGED: small "Mock mode" tag (spec 11.7)
  } catch (error) {
    $('view').innerHTML = `<div class="intro"><div class="card"><strong>Stillspace could not start</strong><p class="sub">${esc(error.message)}</p><button class="primary" id="retryStart">Try again</button></div></div>`;
    $('retryStart').onclick = start;
    return;
  }
  // CHANGED: a code kept in this tab means the person already consented and
  // signed in, so a refresh does not log them out (spec section 12).
  if (participantCode) {
    try {
      applyStatus(await api(`/api/participants/${encodeURIComponent(participantCode)}/status`));
      consent = true;
      routeByStatus();
      return;
    } catch (error) {
      // Unknown code (e.g. the database was deleted): fall back to the consent page.
      status = null;
    }
  }
  render();
}

start();
