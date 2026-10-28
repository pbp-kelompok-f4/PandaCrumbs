// Run with node --test tests/js/app.test.cjs; no npm packages required.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../main/static/main/js/app.js'), 'utf8');
const ok = data => ({ ok: true, redirected: false, json: async () => data });
const tick = () => new Promise(resolve => setImmediate(resolve));
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
function page(fetch, status) {
  const events = {}, filterEvents = {}, calls = [];
  const button = { disabled: false };
  const results = { innerHTML: 'Old cards', busy: false,
    setAttribute() { this.busy = true; }, removeAttribute() { this.busy = false; } };
  const feedback = { hidden: true, textContent: '' };
  const location = { pathname: '/recipes/', origin: 'https://test.invalid', search: '' };
  const form = { dataset: { target: 'results' }, elements: {}, params: [],
    addEventListener(type, handler) { filterEvents[type] = handler; },
    querySelectorAll() { return []; },
    querySelector(s) { return s === '[name=status].selected' && status ? { value: status } : null; } };
  const action = { action: 'https://test.invalid/recipes/1/bookmark/',
    dataset: { action: 'bookmark' }, closest() { return this; }, querySelector() { return button; } };
  const document = {
    querySelector(s) { return s === '[data-filter-form]' ? form : s === '#feedback' ? feedback : null; },
    querySelectorAll(s) { return s === '[data-action] button' ? [button] : []; },
    getElementById() { return results; }, addEventListener(t, h) { events[t] = h; },
  };
  vm.runInNewContext(source, {
    document, location, window: { location }, URL, URLSearchParams, AbortController,
    FormData: class { constructor(f) { return f.params || []; } },
    fetch(url, options) { calls.push({ url: String(url), options }); return fetch(url, options); },
    setTimeout() {}, clearTimeout() {},
    history: { replaceState(_state, _title, url) { location.search = url.search; } },
  });
  return { button, results, feedback, location, calls,
    submit: () => events.submit({ target: action, preventDefault() {} }),
    search(q) { form.params = [['q', q]]; filterEvents.submit({ preventDefault() {} }); },
  };
}

test('saved bookmark with failed refresh locks stale controls until recovery', async () => {
  let offline = true, posts = 0;
  const p = page(async (_url, options) => {
    if (options.method === 'POST') { posts++; return ok({ saved: true }); }
    if (offline) throw new TypeError('Offline');
    return ok({ html: 'Saved cards' });
  });
  await p.submit();
  assert.equal(p.button.disabled, true);
  assert.match(p.feedback.textContent, /tersimpan/i);
  await p.submit();
  assert.equal(posts, 1);
  offline = false;
  p.search('rice'); await tick();
  assert.equal(p.results.innerHTML, 'Saved cards');
  assert.equal(p.feedback.hidden, true);
});

test('bookmark completion refreshes newest pending filter, not old URL', async () => {
  const post = deferred(), old = deferred(); let count = 0;
  const p = page(async (_url, options) => {
    if (options.method === 'POST') return post.promise;
    return ++count === 1 ? old.promise : ok({ html: 'Rice saved' });
  });
  const mutation = p.submit(); p.search('rice');
  post.resolve(ok({ saved: true })); await mutation;
  assert.equal(new URL(p.calls.at(-1).url).searchParams.get('q'), 'rice');
  old.resolve(ok({ html: 'Stale response' })); await tick();
  assert.equal(p.results.innerHTML, 'Rice saved');
});

test('superseded response neither renders nor clears current loading state', async () => {
  const old = deferred(), latest = deferred(); let count = 0;
  const p = page(() => ++count === 1 ? old.promise : latest.promise);
  p.search('rice'); p.search('bread'); old.resolve(ok({ html: 'Rice' })); await tick();
  assert.equal(p.results.busy, true); assert.notEqual(p.results.innerHTML, 'Rice');
  latest.resolve(ok({ html: 'Bread' })); await tick();
  assert.equal(p.results.innerHTML, 'Bread'); assert.equal(p.results.busy, false);
});

test('rejected bookmark enables retry without refreshing', async () => {
  const p = page(async () => ({ ok: false, redirected: false, json: async () => ({ error: 'Invalid action' }) }));
  await p.submit();
  assert.equal(p.button.disabled, false); assert.equal(p.calls.length, 1);
  assert.equal(p.feedback.textContent, 'Invalid action');
});

test('pending bookmark cannot be repeated through a replaced button', async () => {
  const post = deferred(); let posts = 0;
  const p = page(async (_url, options) => {
    if (options.method === 'POST') { posts++; return post.promise; }
    return ok({ html: 'Saved cards' });
  });
  const first = p.submit(); p.button.disabled = false; const second = p.submit();
  assert.equal(posts, 1); post.resolve(ok({ saved: true })); await Promise.all([first, second]);
});

test('mutation preserves the status selected on an initial filtered Pantry page', async () => {
  const p = page(async (_url, options) => options.method === 'POST' ? ok({}) : ok({ html: 'Filtered cards' }), 'safe');
  await p.submit();
  assert.equal(new URL(p.calls.at(-1).url).searchParams.get('status'), 'safe');
});
