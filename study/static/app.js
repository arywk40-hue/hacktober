'use strict';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const state = {subject: '', documents: [], busy: false, questions: [], review: null};
function notice(text = '', error = false) {
  $('#notice').textContent = text;
  $('#notice').hidden = !text;
  $('#notice').classList.toggle('error', error);
}
async function api(path, options = {}) {
  const response = await fetch('/api' + path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  return data;
}
function post(path, data) {
  return api(path, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)});
}
function requireSubject() {
  if (!state.subject) throw new Error('Create a subject first, then add your PDFs.');
}
function requireDocuments() {
  requireSubject();
  if (!state.documents.some(doc => doc.status === 'ready')) throw new Error('Add a PDF, or review and approve your scanned notes first.');
}
function setBusy(value) {
  state.busy = value;
  for (const element of document.querySelectorAll('#upload-submit, #chat-submit, #quiz-submit, #subject-select, #new-subject, #study-document, #quiz-document, .delete-document, [data-review], #review-page, #read-page, #review-text, #review-checked, #approve-review')) element.disabled = value;
}
async function perform(action) {
  if (state.busy) return;
  setBusy(true); notice();
  try { await action(); }
  catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}
function storageRead(key) { try { return localStorage.getItem(key); } catch { return null; } }
function storageWrite(key, value) { try { localStorage.setItem(key, value); } catch { /* Study works without browser storage. */ } }
function showView(view) {
  for (const section of document.querySelectorAll('.view')) section.hidden = section.id !== view;
  for (const button of document.querySelectorAll('nav button')) button.classList.toggle('active', button.dataset.view === view);
}
for (const button of document.querySelectorAll('nav button')) button.onclick = () => showView(button.dataset.view);
async function loadSubjects(selected) {
  const subjects = await api('/subjects');
  $('#subject-select').innerHTML = '<option value="">Choose a subject</option>' + subjects.map(subject => `<option value="${esc(subject.id)}">${esc(subject.title)}</option>`).join('');
  const preferred = selected || storageRead('citetutor.subject');
  state.subject = subjects.some(subject => subject.id === preferred) ? preferred : subjects[0]?.id || '';
  $('#subject-select').value = state.subject;
  $('#subject-label').textContent = subjects.find(subject => subject.id === state.subject)?.title || 'Getting started';
  storageWrite('citetutor.subject', state.subject);
  await loadDocuments();
}
async function loadDocuments() {
  state.documents = state.subject ? await api(`/subjects/${state.subject}/documents`) : [];
  const documents = state.documents;
  $('#document-count').textContent = documents.length;
  $('#page-count').textContent = documents.reduce((sum, doc) => sum + doc.page_count, 0);
  $('#source-total').textContent = documents.length;
  $('#documents').innerHTML = documents.length ? documents.map(doc => `<article class="document-card"><span class="pdf-icon">PDF</span><div class="document-info"><h3>${esc(doc.title)}</h3><p>${doc.page_count} pages · ${doc.unit_count} source chunks${doc.status === 'needs_review' ? ` · ${doc.ocr_pages.length} scans to review` : doc.blank_pages.length ? ` · ${doc.blank_pages.length} page(s) excluded` : ''}</p></div>${doc.status === 'needs_review' ? `<button class="secondary" data-review="${esc(doc.id)}">Review scans</button>` : '<span class="ready-tag">Ready to study</span>'}<button class="delete-document" data-delete="${esc(doc.id)}" aria-label="Remove ${esc(doc.title)}">Remove</button></article>`).join('') : `<div class="empty-state">${state.subject ? 'Your desk is ready. Add a PDF to start studying.' : 'Create a subject to add your first PDF.'}</div>`;
  const ready = documents.filter(doc => doc.status === 'ready');
  const options = ready.map(doc => `<option value="${esc(doc.id)}">${esc(doc.title)}</option>`).join('');
  const previousStudy = $('#study-document').value;
  const previousQuiz = $('#quiz-document').value;
  $('#study-document').innerHTML = '<option value="">All PDFs in this subject</option>' + options;
  $('#quiz-document').innerHTML = ready.length ? options : '<option value="">Add or approve a PDF first</option>';
  if (ready.some(doc => doc.id === previousStudy)) $('#study-document').value = previousStudy;
  if (ready.some(doc => doc.id === previousQuiz)) $('#quiz-document').value = previousQuiz;
  updateRange();
}
function updateRange() {
  const doc = state.documents.find(doc => doc.id === $('#quiz-document').value);
  $('#page-start').max = doc?.page_count || 1;
  $('#page-end').max = doc?.page_count || 1;
  $('#page-start').value = 1;
  $('#page-end').value = Math.min(5, doc?.page_count || 1);
}
$('#quiz-document').onchange = updateRange;
$('#subject-select').onchange = () => perform(async () => {
  const selected = $('#subject-select').value;
  $('#conversation').innerHTML = '<div class="empty-state">Ask a question about this subject’s PDFs.</div>';
  $('#quiz-results').innerHTML = '<div class="empty-state">Choose a document and pages for a new practice set.</div>';
  $('#quiz-summary').hidden = true;
  state.questions = [];
  await loadSubjects(selected);
});
$('#new-subject').onclick = () => { $('#subject-dialog').showModal(); $('#subject-title').focus(); };
$('#cancel-subject').onclick = () => $('#subject-dialog').close();
$('#subject-form').onsubmit = event => {
  event.preventDefault();
  const title = $('#subject-title').value;
  $('#subject-dialog').close();
  perform(async () => {
    const subject = await post('/subjects', {title});
    $('#subject-form').reset();
    $('#conversation').innerHTML = '<div class="empty-state">Add your subject PDFs, then ask a question.</div>';
    $('#quiz-results').replaceChildren(); $('#quiz-summary').hidden = true;
    await loadSubjects(subject.id);
    showView('library');
    notice('Subject created. Add your college notes or textbook chapters.');
  });
};
$('#upload-files').onchange = () => {
  const files = Array.from($('#upload-files').files);
  $('#file-description').textContent = files.length === 1 ? files[0].name : files.length ? `${files.length} PDFs selected` : 'No files selected';
};
$('#upload-form').onsubmit = event => {
  event.preventDefault();
  perform(async () => {
    requireSubject();
    const files = Array.from($('#upload-files').files);
    try {
      for (let i = 0; i < files.length; i++) {
        notice(`Reading ${files[i].name} (${i + 1}/${files.length}) on your laptop…`);
        const body = new FormData(); body.append('subject_id', state.subject); body.append('file', files[i]);
        body.append('force_scan', $('#force-scan').checked);
        await api('/documents', {method:'POST', body});
      }
      $('#upload-form').reset(); $('#file-description').textContent = 'No files selected';
      notice('PDFs added. Review any scanned pages on your desk before studying them.');
    } finally { await loadDocuments(); }
  });
};
$('#refresh').onclick = () => { if (!state.busy) perform(loadDocuments); };
$('#documents').onclick = event => {
  const review = event.target.closest('[data-review]');
  if (review && !state.busy) { perform(() => openReview(review.dataset.review)); return; }
  const button = event.target.closest('[data-delete]');
  if (!button || state.busy) return;
  const doc = state.documents.find(doc => doc.id === button.dataset.delete);
  if (!window.confirm(`Remove ${doc?.title || 'this PDF'} and its local index?`)) return;
  perform(async () => {
    await api(`/documents/${button.dataset.delete}`, {method:'DELETE'});
    $('#conversation').innerHTML = '<div class="empty-state">Material changed. Ask a new question about the remaining PDFs.</div>';
    $('#quiz-results').replaceChildren(); $('#quiz-summary').hidden = true; state.questions = [];
    await loadDocuments(); notice('PDF and its local index removed.');
  });
};
async function openReview(id) {
  const result = await api(`/documents/${id}/review`);
  if (result.document.status !== 'needs_review') throw new Error('This document is already approved. Refresh your desk.');
  state.review = {...result, index: 0, checked: new Set()};
  $('#review-title').textContent = result.document.title;
  $('#review-page').innerHTML = result.pages.map((p, i) => `<option value="${i}">Page ${p.page}</option>`).join('');
  $('#review-status').textContent = 'Choose a page, read it locally, then correct and check the text against the image.';
  renderReview();
  $('#review-dialog').showModal();
}
function renderReview() {
  const review = state.review, page = review.pages[review.index];
  $('#review-page').value = review.index;
  $('#review-image').src = `/api/documents/${review.document.id}/pages/${page.page}/image`;
  $('#review-image').alt = `Original PDF page ${page.page}`;
  $('#review-text').value = page.text;
  $('#review-checked').checked = review.checked.has(page.page);
  $('#review-progress').textContent = `${review.checked.size}/${review.pages.length} scanned pages checked`;
}
$('#review-page').onchange = () => { state.review.index = Number($('#review-page').value); renderReview(); };
$('#review-text').oninput = () => {
  const review = state.review, page = review.pages[review.index];
  page.text = $('#review-text').value;
  review.checked.delete(page.page);
  $('#review-checked').checked = false;
  $('#review-progress').textContent = `${review.checked.size}/${review.pages.length} scanned pages checked`;
};
$('#review-checked').onchange = () => {
  const review = state.review, page = review.pages[review.index];
  if ($('#review-checked').checked) review.checked.add(page.page); else review.checked.delete(page.page);
  $('#review-progress').textContent = `${review.checked.size}/${review.pages.length} scanned pages checked`;
};
$('#read-page').onclick = () => perform(async () => {
  const review = state.review, page = review.pages[review.index];
  if (page.text && !window.confirm('Replace this page’s draft and your edits with a new local transcription?')) return;
  $('#review-status').textContent = 'Reading this page with local Gemma… Allow a few minutes on a laptop.';
  try {
    const draft = await post(`/documents/${review.document.id}/pages/${page.page}/ocr`, {});
    page.text = draft.text;
    review.checked.delete(page.page);
    renderReview();
    $('#review-status').textContent = 'Unverified draft. Check every line, especially numbers and equations. Correct mistakes or remove unreadable lines.';
  } catch (error) { $('#review-status').textContent = error.message; throw error; }
});
$('#approve-review').onclick = () => perform(async () => {
  const review = state.review;
  if (review.checked.size !== review.pages.length) {
    $('#review-status').textContent = 'Check every scanned page against its image before approval. Leave unreadable pages blank to exclude them.';
    return;
  }
  $('#review-status').textContent = 'Indexing your approved text locally…';
  try {
    await post(`/documents/${review.document.id}/review`, {version: review.version,
      pages: review.pages.map(p => ({page: p.page, text: p.text}))});
    $('#review-dialog').close(); state.review = null;
    await loadDocuments(); notice('Reviewed notes are ready to study. Click citations to compare the text with the original page.');
  } catch (error) { $('#review-status').textContent = error.message; throw error; }
});
$('#close-review').onclick = () => $('#review-dialog').close();
function citations(items) {
  return items.map(c => `<button class="cite" data-source="${esc(c.document_id)}" data-page="${c.page}" data-quote="${esc(c.quote || '')}">${esc(c.label)} ${esc(c.document_title)} ↗</button>`).join('');
}
$('#chat-form').onsubmit = event => {
  event.preventDefault();
  perform(async () => {
    requireDocuments();
    const message = $('#message').value;
    const selected = $('#study-document').value;
    $('#conversation .empty-state')?.remove();
    const user = document.createElement('div'); user.className = 'message user'; user.textContent = message;
    $('#conversation').append(user); $('#message').value = '';
    const loading = document.createElement('div'); loading.className = 'message loading';
    loading.innerHTML = '<span class="spinner" aria-hidden="true"></span> Reading your notes and checking the answer…';
    $('#conversation').append(loading); loading.scrollIntoView({block:'nearest'});
    try {
      const result = await post('/chat', {subject_id:state.subject, message, mode:$('#study-mode').value,
        style:$('#study-style').value, document_ids:selected ? [selected] : []});
      loading.classList.remove('loading');
      loading.innerHTML = result.declined ? `<p>${esc(result.reason)}</p><small>Try another topic or add a PDF that covers your question.</small>` : result.segments.map(s => `<p>${esc(s.text)}</p>${citations(s.citations)}`).join('') + '<small>Checked against the cited evidence by a separate local model.</small>';
    } catch (error) { loading.textContent = error.message; throw error; }
    $('#conversation').scrollTop = $('#conversation').scrollHeight;
  });
};
document.addEventListener('click', async event => {
  const prompt = event.target.closest('[data-prompt]');
  if (prompt) { $('#message').value = prompt.dataset.prompt; $('#message').focus(); }
  const link = event.target.closest('[data-source]');
  if (!link) return;
  $('#source-title').textContent = 'Loading source…'; $('#source-text').textContent = '';
  $('#source-quote').hidden = true;
  $('#source-image').hidden = true; $('#source-provenance').textContent = '';
  if (!$('#source-dialog').open) $('#source-dialog').showModal();
  try {
    const page = await api(`/documents/${link.dataset.source}/pages/${link.dataset.page}`);
    $('#source-title').textContent = `${page.title} · Page ${page.page}`;
    $('#source-text').textContent = page.text || 'This page contains no approved text.';
    if (page.extraction === 'local_ocr') {
      $('#source-provenance').textContent = 'Human-reviewed scan transcription. Verification checks this text; compare it with the original page below.';
      $('#source-image').src = `/api/documents/${link.dataset.source}/pages/${page.page}/image`;
      $('#source-image').alt = `Original PDF page ${page.page}`; $('#source-image').hidden = false;
    }
    if (link.dataset.quote) { $('#source-quote').textContent = link.dataset.quote; $('#source-quote').hidden = false; }
  } catch (error) { $('#source-title').textContent = 'Source unavailable'; $('#source-text').textContent = error.message; }
});
$('#close-source').onclick = () => $('#source-dialog').close();
$('#quiz-form').onsubmit = event => {
  event.preventDefault();
  perform(async () => {
    requireDocuments();
    const type = $('#question-type').value;
    const start = Number($('#page-start').value), end = Number($('#page-end').value);
    if (start > end || end - start >= 20) throw new Error('Choose a range of 1–20 pages with the first page before the last.');
    $('#quiz-summary').hidden = false;
    $('#quiz-summary').innerHTML = '<span class="spinner" aria-hidden="true"></span> Writing questions, solving them independently, and checking source support…';
    $('#quiz-results').replaceChildren();
    try {
      const result = await post('/quizzes', {subject_id:state.subject, document_id:$('#quiz-document').value,
        page_start:start, page_end:end, count:Number($('#question-count').value), types:type === 'mixed' ? ['mcq','short'] : [type]});
      state.questions = result.questions;
      $('#quiz-summary').innerHTML = `<strong>${result.accepted} verified · ${result.rejected} rejected</strong> from ${result.requested} candidates.` + (result.rejected ? '<details><summary>Why were questions rejected?</summary>' + Object.entries(result.rejection_summary).map(([reason, count]) => `<div>${esc(reason)}: ${count}</div>`).join('') + '</details>' : '');
      $('#quiz-results').innerHTML = result.questions.length ? result.questions.map((q, index) => `<article class="card quiz-card"><div class="eyebrow">QUESTION ${index + 1} · ${q.type === 'mcq' ? 'MULTIPLE CHOICE' : 'SHORT ANSWER'}</div><h2>${esc(q.stem)}</h2><form class="practice-answer" data-question="${index}">${q.type === 'mcq' ? `<fieldset><legend>Choose an answer</legend>${q.options.map(o => `<label class="quiz-option"><input type="radio" name="answer" value="${esc(o.id)}" required><span><strong>${esc(o.id)}.</strong> ${esc(o.text)}</span></label>`).join('')}</fieldset>` : '<label>Your answer<textarea name="answer" placeholder="Explain it in your own words…" required></textarea></label>'}<button type="submit" class="secondary">${q.type === 'mcq' ? 'Check my answer' : 'Compare with source answer'}</button><div class="quiz-feedback" aria-live="polite"></div></form><details class="source-answer"><summary>Show answer & supporting evidence</summary><p><strong>Source answer:</strong> ${esc(displayAnswer(q))}</p><p>${esc(q.rationale)}</p>${q.citations.map(c => `<blockquote class="quote">“${esc(c.quote)}”</blockquote>${citations([c])}`).join('')}</details></article>`).join('') : '<div class="empty-state"><h2>No questions passed verification.</h2><p>Choose a different page range or try a smaller practice set.</p></div>';
    } catch (error) { $('#quiz-summary').textContent = 'Practice set could not be completed.'; throw error; }
  });
};
function displayAnswer(question) {
  return question.type === 'mcq' ? `${question.answer}. ${question.options.find(o => o.id === question.answer)?.text || ''}` : question.answer;
}
$('#quiz-results').addEventListener('submit', event => {
  const form = event.target.closest('.practice-answer');
  if (!form) return;
  event.preventDefault();
  const q = state.questions[Number(form.dataset.question)];
  const value = new FormData(form).get('answer');
  const feedback = form.querySelector('.quiz-feedback');
  if (q.type === 'mcq') {
    const correct = value === q.answer;
    feedback.classList.toggle('wrong', !correct);
    feedback.textContent = correct ? 'That’s right. Read the source evidence below to check your reasoning.' : `Revisit this one. The source answer is ${displayAnswer(q)}.`;
  } else { feedback.textContent = 'Compare your explanation with the verified source answer below. Short answers are for self-review.'; }
  form.parentElement.querySelector('.source-answer').open = true;
});
async function health() {
  const response = await api('/health');
  const tracingOn = response.tracing?.status === 'enabled';
  $('.privacy-label').textContent = tracingOn ? '◉ Local AI · Sentry metadata' : '◉ Local & private';
  $('.privacy-label').title = tracingOn ? 'Sentry receives timings, token counts and rejection codes. Notes and answers stay local.' : 'Models and documents stay local. Sentry tracing is off.';
  $('#model-status').textContent = response.models.ready ? 'All models ready' : 'Setup needed';
  $('#models').innerHTML = Object.entries(response.models.roles).map(([role, model]) => `<p><span>${esc(role)}</span><code>${esc(model.model)}</code><span>${model.ready ? 'Ready' : esc(model.error)}</span></p>`).join('');
}
Promise.all([loadSubjects(), health()]).catch(error => notice(error.message, true));
