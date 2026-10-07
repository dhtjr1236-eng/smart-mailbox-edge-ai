# Dashboard repair and verification

`frontend/app.js` now builds cards with DOM nodes and `textContent`, and attaches
listeners with `addEventListener`. Untrusted labels/analysis never become markup
or inline event-handler code. Images are restricted to HTTP(S), same-origin,
`/static/images/<simple-name>.jpg|jpeg|png|webp` URLs, without credentials, query
strings or fragments. Zero confidence displays as `0.0%`. Failed/invalid images
show a placeholder in both the card and modal. Existing filter, pagination, theme,
refresh and modal controls remain available; cards also support Enter/Space.

## Reproduce tests

Node.js 20+ and npm are needed only for development tests, not for the dashboard.

```bash
node --check frontend/app.js
npm ci --prefix tests
npm test --prefix tests
```

The eight jsdom tests exercise the actual HTML and JavaScript with mocked fetch:
normal/empty results, HTTP/network failures and recovery, untrusted text, unsafe
URLs, image error events, filters/pagination/date selection, modal and keyboard/
theme controls. Image failures are dispatched events; jsdom does not validate
real image decoding, layout or browser rendering.

A separate Chromium suite is provided for environments with browser downloads:

```bash
cd tests
npx playwright install chromium
npm run test:browser
```

The browser suite serves the frontend in isolation and mocks the API, so it does
not certify the existing Flask/Docker static routing or live database integration.
During this repair, Chromium installation failed because downloaded archives were
invalid/truncated. The browser suite has not been executed successfully. The eight
DOM tests and `node --check` passed. Real browser visual verification remains open.

## Scope

This repair does not change the current-page statistics or UTC-based date count,
auto-refresh scheduling, Docker/static server paths, authentication, or backend
API. Those remain the separate follow-up work identified in the review.
