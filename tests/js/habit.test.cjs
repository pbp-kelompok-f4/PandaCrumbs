const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../habit_challenge/static/habit_challenge/habit.js'), 'utf8');

function page(fetch) {
  function element() {
    return { events: {}, attrs: {}, textContent: '', isConnected: true,
      addEventListener(type, handler) { this.events[type] = handler; },
      setAttribute(key, value) { this.attrs[key] = value; },
      getAttribute(key) { return this.attrs[key]; },
      removeAttribute(key) { delete this.attrs[key]; },
      focus() { this.focused = true; },
      append(child) { child.parentElement = this; },
      showModal() { this.open = true; },
      close() { this.open = false; queueMicrotask(() => this.events.close?.()); },
    };
  }
  const ids = Object.fromEntries(['habit-dashboard', 'habit-checkin-dialog', 'habit-success-dialog',
    'habit-checkin-description', 'habit-dialog-form', 'habit-success-title', 'habit-success-food',
    'habit-success-reward', 'feedback'].map(id => [id, element()]));
  const dashboard = ids['habit-dashboard'], dialog = ids['habit-checkin-dialog'];
  const form = element(), home = element(), trigger = element(), button = element(), errors = element(), close = element();
  form.elements = { food: { value: 'Sup sayur', focus() {} } };
  form.action = '/habit-challenge/share/complete/';
  form.closest = () => form;
  form.querySelector = selector => selector === 'button[type="submit"]' ? button : errors;
  home.dataset = { challengeTitle: 'Berbagi makanan' };
  home.querySelector = selector => selector === 'summary' ? trigger : form;
  home.append(form);
  trigger.parentElement = home;
  trigger.closest = () => trigger;
  const heading = element();
  dashboard.querySelector = selector => selector === '.habit-title' ? heading : null;
  dialog.querySelector = () => close;
  const classes = new Set();
  vm.runInNewContext(source, { document: { querySelector: s => ids[s.slice(1)] || null,
    body: { classList: { add: c => classes.add(c), remove: c => classes.delete(c) } } },
    fetch, window: { location: { assign() {} } }, FormData: class {}, setTimeout() {}, URLSearchParams });
  return { ids, dialog, form, home, trigger, button, errors, close, classes,
    open: () => dashboard.events.click({ target: trigger, preventDefault() {} }),
    submit: () => dialog.events.submit({ target: form, preventDefault() {} }),
  };
}
const response = (created = true) => ({ ok: true, json: async () => ({ html: '<h1>Updated</h1>',
  completion: { created, food: 'Sup <sayur>', points: created ? 15 : 0, action: 'dibagikan', reward: 'setelah berbagi' } }) });

test('closing check-in restores the form and draft to its original card', async () => {
  const p = page(async () => response());
  p.open();
  assert.equal(p.dialog.open, true);
  assert.equal(p.form.parentElement, p.ids['habit-dialog-form']);
  p.dialog.close();
  await Promise.resolve();
  assert.equal(p.form.parentElement, p.home);
  assert.equal(p.form.elements.food.value, 'Sup sayur');
  assert.equal(p.trigger.focused, true);
  assert.equal(p.classes.size, 0);
});

test('validation failure keeps the modal and entered data available for retry', async () => {
  const p = page(async () => ({ ok: false, json: async () => ({ errors: { food: [{ message: 'Isi makanan.' }] } }) }));
  p.open(); await p.submit();
  assert.equal(p.dialog.open, true);
  assert.equal(p.errors.textContent, 'Isi makanan.');
  assert.equal(p.button.disabled, false);
  assert.equal(p.close.disabled, false);
  assert.equal(p.ids['habit-success-dialog'].open, undefined);
});

test('pending check-in blocks duplicate requests and Escape; success shows the server reward', async () => {
  let resolve, calls = 0;
  const pending = new Promise(done => { resolve = done; });
  const p = page(() => { calls++; return pending; });
  p.open();
  const submitted = p.submit();
  await p.submit();
  let prevented = false;
  p.dialog.events.cancel({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(calls, 1);
  resolve(response()); await submitted;
  assert.equal(p.dialog.open, false);
  assert.equal(p.ids['habit-success-dialog'].open, true);
  assert.equal(p.ids['habit-success-food'].textContent, 'Sup <sayur> berhasil dibagikan');
  assert.equal(p.ids['habit-success-reward'].textContent, '+15 poin setelah berbagi');
  p.ids['habit-success-dialog'].close(); await Promise.resolve();
  assert.equal(p.classes.size, 0);
});

test('duplicate completion never claims that new points were added', async () => {
  const p = page(async () => response(false));
  p.open(); await p.submit();
  assert.equal(p.ids['habit-success-title'].textContent, 'Tantangan sudah tercatat');
  assert.doesNotMatch(p.ids['habit-success-reward'].textContent, /\+\d/);
});
