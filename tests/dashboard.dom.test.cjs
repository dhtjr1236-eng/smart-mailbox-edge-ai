const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const html = fs.readFileSync(path.join(__dirname, '../frontend/index.html'), 'utf8');
const script = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');
const sample = {id: 1, detected: true, confidence: 0, label: 'mail', gemini_result: '분석 결과',
  image_url: '/static/images/test.jpg', timestamp: '2026-10-07T10:00:00Z'};

async function setup(t, results = [sample], total = results.length) {
  const dom = new JSDOM(html, {url: 'http://localhost:5000/', runScripts: 'outside-only'});
  t.after(() => dom.window.close());
  const win = dom.window;
  win.matchMedia = () => ({matches: false});
  win.setInterval = () => 0;
  win.console.error = () => {};
  const requests = [];
  win.fetch = async url => { requests.push(new URL(url, win.location.origin)); return {ok: true, json: async () => ({total, results})}; };
  win.eval(script);
  // Drain the initial fetch/json continuations.
  await new Promise(resolve => setImmediate(resolve));
  const query = selector => win.document.querySelector(selector);
  return {win, query, requests};
}

test('normal rendering shows 0% and supports modal click/escape', async t => {
  const {win, query} = await setup(t);
  assert.equal(query('.record-conf').textContent, '신뢰도: 0.0%');
  query('.record-card').click();
  assert.ok(query('#image-modal').classList.contains('open'));
  assert.match(query('#modal-desc').textContent, /분석 결과/);
  assert.equal(query('#modal-img').src, 'http://localhost:5000/static/images/test.jpg');
  win.document.dispatchEvent(new win.KeyboardEvent('keydown', {key: 'Escape'}));
  assert.ok(!query('#image-modal').classList.contains('open'));
});

test('empty results render a message and disabled pagination', async t => {
  const {query} = await setup(t, []);
  assert.match(query('#records-grid').textContent, /기록이 없습니다/);
  assert.ok(query('#btn-next').disabled);
  assert.ok(query('#btn-prev').disabled);
});

test('HTTP and network errors display safely; refresh recovers', async t => {
  const {win, query} = await setup(t);
  win.fetch = async () => ({ok: false, status: 503});
  query('#btn-refresh').click();
  await new Promise(resolve => setImmediate(resolve));
  assert.match(query('#records-grid').textContent, /HTTP 503/);
  win.fetch = async () => { throw new Error('<img src=x onerror=alert(1)>'); };
  query('#btn-refresh').click();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(query('#records-grid img'), null);
  assert.match(query('#records-grid').textContent, /<img/);
  win.fetch = async () => ({ok: true, json: async () => ({total: 1, results: [sample]})});
  query('#btn-refresh').click();
  await new Promise(resolve => setImmediate(resolve));
  assert.ok(query('.record-card'));
});

test('untrusted text remains literal in cards and modal', async t => {
  const attack = `<img src=x onerror="window.pwned=1"> ' ");window.pwned=2;// & <script>window.pwned=3</script>`;
  const {win, query} = await setup(t, [{...sample, label: attack, gemini_result: attack}]);
  assert.equal(query('.record-label').textContent, attack);
  assert.equal(query('.record-card script, [onclick], [onerror], [onchange]'), null);
  query('.record-card').click();
  assert.ok(query('#modal-desc').textContent.includes(attack));
  assert.equal(win.pwned, undefined);
});

test('image policy rejects executable, cross-origin and traversal URLs', async t => {
  const values = ['javascript:alert(1)', 'data:image/svg+xml,<svg/>', 'https://example.com/test.jpg',
    '//example.com/test.jpg', '/static/images/../../secret.jpg', '/static/images/%2e%2e/test.jpg',
    '/static/images/test.svg', '/static/images/test.jpg?token=secret', 'http://user:pass@localhost:5000/static/images/a.jpg'];
  const {win, query} = await setup(t, values.map(url => ({...sample, image_url: url})));
  assert.equal(query('.record-img'), null);
  assert.equal(win.document.querySelectorAll('.record-img-placeholder').length, values.length);
  query('.record-card').click();
  assert.equal(query('#modal-img').getAttribute('src'), null);
  assert.equal(query('#modal-image-fallback').hidden, false);
});

test('image error events replace thumbnails and expose modal fallback', async t => {
  const {win, query} = await setup(t);
  query('.record-img').dispatchEvent(new win.Event('error'));
  assert.ok(query('.record-img-placeholder'));
  assert.equal(query('.record-img'), null);
  query('.record-card').click();
  query('#modal-img').dispatchEvent(new win.Event('error'));
  assert.equal(query('#modal-img').style.display, 'none');
  assert.equal(query('#modal-image-fallback').hidden, false);
});

test('pagination and filters send correct queries and reset page', async t => {
  const {win, query, requests} = await setup(t, [sample], 41);
  async function click(selector) {
    query(selector).click();
    await new Promise(resolve => setImmediate(resolve));
  }
  await click('#btn-next');
  assert.equal(requests.at(-1).searchParams.get('page'), '2');
  await click('#btn-prev');
  assert.equal(requests.at(-1).searchParams.get('page'), '1');
  await click('#btn-next');
  await click('#btn-detected');
  assert.equal(requests.at(-1).searchParams.get('page'), '1');
  assert.equal(requests.at(-1).searchParams.get('detected_only'), 'true');
  query('#date-filter').value = '2026-10-07';
  query('#date-filter').dispatchEvent(new win.Event('change'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(requests.at(-1).searchParams.get('date'), '2026-10-07');
  await click('#btn-all');
  assert.equal(requests.at(-1).searchParams.has('detected_only'), false);
});

test('keyboard activation, modal close button, and theme toggle', async t => {
  const {win, query} = await setup(t);
  query('.record-card').dispatchEvent(new win.KeyboardEvent('keydown', {key: 'Enter'}));
  assert.ok(query('#image-modal').classList.contains('open'));
  query('.modal-close').click();
  assert.ok(!query('#image-modal').classList.contains('open'));
  query('[data-theme-toggle]').click();
  assert.equal(win.document.documentElement.getAttribute('data-theme'), 'dark');
});
