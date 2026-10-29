// Uses an isolated test database/session supplied by Django's live-server test.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ channel: process.env.AUDIT_BROWSER_CHANNEL || 'chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    const base = process.env.AUDIT_BROWSER_URL;
    await context.addCookies([{ name: 'sessionid', value: process.env.AUDIT_BROWSER_SESSION, url: base }]);
    const page = await context.newPage();
    page.setDefaultTimeout(12000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/waste-audit/');
    await page.evaluate(() => { window.auditNoReload = true; });
    const rows = page.locator('.audit-table tbody tr');
    const checkRows = async count => {
      await page.waitForFunction(n => document.querySelectorAll('.audit-table tbody tr').length === n, count);
      assert.equal(await rows.count(), count);
      assert.equal(await page.evaluate(() => window.auditNoReload), true, 'Unexpected document reload');
      assert.ok(!(await page.locator('#audit-results').innerText()).includes('Ayam rahasia'));
    };
    const filter = async (query, enter = false) => {
      await page.locator('[name=q]').fill(query);
      const response = page.waitForResponse(r => r.url().includes('/waste-audit/?') && r.request().resourceType() === 'fetch');
      if (enter) await page.locator('[name=q]').press('Enter');
      else await page.locator('#audit-filter-submit').click();
      assert.equal((await response).status(), 200);
      await page.waitForFunction(() => !document.querySelector('#audit-results').hasAttribute('aria-busy'));
    };
    const reset = async () => {
      await page.locator('[data-audit-reset]').first().click();
      await page.waitForFunction(() => !location.search && !document.querySelector('#audit-results').hasAttribute('aria-busy'));
    };
    const dialog = page.locator('#audit-dialog');
    const openAdd = async () => {
      await page.locator('.audit-heading [data-audit-open]').click();
      await dialog.locator('[name=food_name]').waitFor();
    };
    const save = async () => {
      await dialog.locator('button[type=submit]').click();
      await dialog.waitFor({ state: 'hidden' });
      await page.waitForFunction(() => !document.querySelector('#audit-results').hasAttribute('aria-busy'));
      assert.equal(await page.locator('#audit-filter-submit').evaluate(el => el === document.activeElement), true);
    };
    await checkRows(2);
    await filter('  AYAM  ', true);
    await checkRows(1);
    assert.ok((await rows.innerText()).includes('Ayam goreng'));
    assert.ok(!(await page.locator('#audit-results').innerText()).includes('Bayam'));
    await filter('goreng');
    await checkRows(1);
    assert.ok((await page.locator('.audit-loss-value').innerText()).includes('5.000'));
    await page.locator('[name=reason]').selectOption('excess');
    await filter('ayam');
    await checkRows(0);
    await reset();
    await checkRows(2);
    assert.equal(await page.locator('[name=q]').inputValue(), '');
    await filter('pizza');
    await page.getByRole('heading', { name: 'Belum ada catatan yang cocok.' }).waitFor();
    await reset();
    await filter('ayam');
    await openAdd();
    await dialog.locator('[name=food_name]').fill('Ayam browser');
    await dialog.locator('[name=quantity]').fill('2');
    await dialog.locator('[name=unit]').selectOption('pcs');
    await dialog.locator('[name=reason]').selectOption('excess');
    await dialog.locator('[name=estimated_loss]').fill('7000');
    await save();
    await checkRows(2);
    assert.ok(new URL(page.url()).searchParams.get('q') === 'ayam');
    await rows.filter({ hasText: 'Ayam browser' }).getByRole('link', { name: 'Ubah catatan Ayam browser', exact: true }).click();
    await dialog.locator('[name=food_name]').fill('Tahu browser');
    await save();
    await checkRows(1);
    await reset();
    await checkRows(3);
    const changed = rows.filter({ hasText: 'Tahu browser' });
    await changed.getByRole('link', { name: 'Hapus catatan Tahu browser', exact: true }).click();
    await dialog.locator('[data-audit-cancel]').click();
    await dialog.waitFor({ state: 'hidden' });
    await checkRows(3);
    await changed.getByRole('link', { name: 'Hapus catatan Tahu browser', exact: true }).click();
    await save();
    await checkRows(2);
    await openAdd();
    await dialog.locator('[name=food_name]').fill('Input salah');
    await dialog.locator('[name=quantity]').fill('0');
    await dialog.locator('[name=unit]').selectOption('pcs');
    await dialog.locator('[name=reason]').selectOption('spoiled');
    await dialog.locator('form').evaluate(form => { form.noValidate = true; });
    await dialog.locator('button[type=submit]').click();
    await dialog.locator('.audit-errors').waitFor();
    assert.equal(await dialog.locator('[name=food_name]').inputValue(), 'Input salah');
    await dialog.locator('[data-audit-cancel]').click();
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 844 });
      await filter('ayam');
      await checkRows(1);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Mobile horizontal overflow');
      await reset();
    }
    assert.deepEqual(errors, [], 'Browser JavaScript errors');
    const guest = await browser.newPage();
    await guest.goto(base + '/waste-audit/');
    assert.ok(new URL(guest.url()).pathname.includes('/accounts/login/'));
    console.log('Browser OK: search/Enter/reset, private history, AJAX CRUD, validation, keyboard focus, mobile 390/320, guest redirect.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
