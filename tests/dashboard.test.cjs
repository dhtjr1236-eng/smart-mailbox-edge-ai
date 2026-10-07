const {test, before, after, beforeEach, afterEach} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

let server, browser, page, base, errors;
const sample = {id: 1, detected: true, confidence: 0, label: 'mail',
  gemini_result: '분석 결과', image_url: '/static/images/test.jpg', timestamp: '2026-10-07T10:00:00Z'};
const pixel = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64');

before(async () => {
  // Isolate frontend repair from the existing Flask/Docker routing defects.
  server = http.createServer((req, res) => {
    const name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[req.url];
    if (!name) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', name.endsWith('.js') ? 'text/javascript' : name.endsWith('.css') ? 'text/css' : 'text/html');
    res.end(fs.readFileSync(path.join(__dirname, '../frontend', name)));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless: true});
});
after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});
beforeEach(async () => {
  page = await browser.newPage();
  errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/static/images/**', route => route.fulfill({contentType: 'image/png', body: pixel}));
});
afterEach(async () => {
  await page.close();
  assert.deepEqual(errors, [], 'No unhandled browser JavaScript errors');
});
async function load(results = [sample], total = results.length) {
  await page.route('**/api/detections?*', route => route.fulfill({json: {total, results}}));
  await page.goto(base);
  await page.waitForFunction(() => !document.querySelector('#records-grid').textContent.includes('데이터 불러오는 중'));
}

test('normal cards display zero confidence and open/close the image modal', async () => {
  await load();
  assert.equal(await page.locator('.record-conf').textContent(), '신뢰도: 0.0%');
  assert.equal(await page.locator('.record-label').textContent(), 'mail');
  await page.locator('.record-card').click();
  assert.equal(await page.locator('#image-modal').evaluate(n => n.classList.contains('open')), true);
  assert.match(await page.locator('#modal-desc').textContent(), /분석 결과/);
  await page.waitForFunction(() => document.querySelector('#modal-img').naturalWidth > 0);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#image-modal').evaluate(n => n.classList.contains('open')), false);
});

test('empty list and disabled pagination', async () => {
  await load([]);
  assert.match(await page.locator('#records-grid').textContent(), /기록이 없습니다/);
  assert.equal(await page.locator('#btn-prev').isDisabled(), true);
  assert.equal(await page.locator('#btn-next').isDisabled(), true);
});

test('API failure is shown and refresh recovers', async () => {
  let fail = true;
  await page.route('**/api/detections?*', route => fail ? route.fulfill({status: 503, body: 'offline'}) : route.fulfill({json: {total: 1, results: [sample]}}));
  await page.goto(base);
  await page.waitForFunction(() => document.querySelector('#records-grid').textContent.includes('HTTP 503'));
  fail = false;
  await page.locator('#btn-refresh').click();
  await page.locator('.record-card').waitFor();
});

test('untrusted text is literal, not executable markup or event code', async () => {
  const attack = `<img src=x onerror="window.pwned=1"> ' ");window.pwned=2;// & <script>window.pwned=3</script>`;
  await load([{...sample, label: attack, gemini_result: attack}]);
  assert.equal(await page.locator('.record-label').textContent(), attack);
  assert.equal(await page.locator('.record-card script, .record-card [onclick], .record-card [onerror]').count(), 0);
  await page.locator('.record-card').click();
  assert.ok((await page.locator('#modal-desc').textContent()).includes(attack));
  assert.equal(await page.evaluate(() => window.pwned), undefined);
});

test('unsafe image URLs never become image requests', async () => {
  const values = ['javascript:alert(1)', 'data:image/svg+xml,<svg/>', 'https://example.com/test.jpg',
    '//example.com/test.jpg', '/static/images/../../secret.jpg', '/static/images/%2e%2e/test.jpg',
    '/static/images/test.svg', '/static/images/test.jpg?token=secret', 'https://user:pass@example.com/a.jpg'];
  await load(values.map((url, index) => ({...sample, id: index, image_url: url})));
  assert.equal(await page.locator('.record-img').count(), 0);
  assert.equal(await page.locator('.record-img-placeholder').count(), values.length);
  await page.locator('.record-card').first().click();
  assert.equal(await page.locator('#modal-img').getAttribute('src'), null);
});

test('failed images have a visible fallback in cards and modal', async () => {
  await page.unroute('**/static/images/**');
  await page.route('**/static/images/**', route => route.fulfill({status: 404, body: ''}));
  await load();
  await page.locator('.record-img-placeholder').waitFor();
  await page.locator('.record-card').click();
  await page.locator('#modal-image-fallback').waitFor({state: 'visible'});
  assert.equal(await page.locator('#modal-img').isVisible(), false);
});

test('filters, date, and pagination send the requested query and reset page', async () => {
  const queries = [];
  await page.route('**/api/detections?*', route => {
    queries.push(new URL(route.request().url()).searchParams);
    return route.fulfill({json: {total: 41, results: [sample]}});
  });
  await page.goto(base);
  await page.locator('.record-card').waitFor();
  async function clickAndWait(selector) {
    const response = page.waitForResponse(r => r.url().includes('/api/detections?'));
    await page.locator(selector).click();
    await response;
    await page.locator('.record-card').waitFor();
  }
  await clickAndWait('#btn-next');
  assert.equal(queries.at(-1).get('page'), '2');
  await clickAndWait('#btn-prev');
  assert.equal(queries.at(-1).get('page'), '1');
  await clickAndWait('#btn-next');
  await clickAndWait('#btn-detected');
  assert.equal(queries.at(-1).get('detected_only'), 'true');
  assert.equal(queries.at(-1).get('page'), '1');
  const response = page.waitForResponse(r => r.url().includes('date=2026-10-07'));
  await page.locator('#date-filter').fill('2026-10-07');
  await response;
  await page.locator('.record-card').waitFor();
  assert.equal(queries.at(-1).get('date'), '2026-10-07');
  await clickAndWait('#btn-all');
  assert.equal(queries.at(-1).has('detected_only'), false);
});

test('keyboard opens cards and theme toggle still works', async () => {
  await load();
  await page.locator('.record-card').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#image-modal').evaluate(n => n.classList.contains('open')), true);
  await page.locator('.modal-close').click();
  const previous = await page.locator('html').getAttribute('data-theme');
  await page.locator('[data-theme-toggle]').click();
  assert.notEqual(await page.locator('html').getAttribute('data-theme'), previous);
});
