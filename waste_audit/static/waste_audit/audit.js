(() => {
  if (!document.body.classList.contains('audit-body')) return;
  const indexUrl = document.querySelector('[data-audit-index]').dataset.auditIndex;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let motionPaused = false;
  let filterRequest;
  let openingRequest;
  let opener;
  let mutating = false;
  try { motionPaused = localStorage.getItem('audit-motion-paused') === 'true'; } catch {}

  const updateMotion = () => {
    document.body.classList.toggle('audit-motion-paused', motionPaused);
    const button = document.querySelector('.audit-motion-toggle');
    if (!button) return;
    button.hidden = reducedMotion.matches;
    button.setAttribute('aria-pressed', String(motionPaused));
    button.textContent = motionPaused ? 'Lanjutkan animasi latar' : 'Jeda animasi latar';
  };
  reducedMotion.addEventListener('change', updateMotion);
  updateMotion();

  const announce = (message) => {
    const box = document.querySelector('#audit-filter-status') || document.querySelector('#feedback');
    box.hidden = false;
    box.textContent = message;
  };
  const dialogStatus = (message) => {
    const box = document.querySelector('#audit-dialog-status');
    if (box) box.textContent = message;
  };
  const request = async (url, options = {}) => {
    const response = await fetch(url, {
      credentials: 'same-origin',
      ...options,
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        ...options.headers,
      },
    });
    if (response.redirected && new URL(response.url).pathname.includes('/accounts/login/')) {
      location.assign(response.url);
      throw new Error('Sesi berakhir. Silakan masuk kembali.');
    }
    const data = await response.json().catch(() => {
      throw new Error(response.status === 403
        ? 'Token keamanan tidak berlaku. Muat ulang halaman lalu coba lagi.'
        : response.status === 404
          ? 'Catatan tidak ditemukan atau tidak dapat diakses.'
          : 'Respons server tidak valid. Coba lagi setelah memeriksa koneksi.');
    });
    if (!response.ok && response.status !== 422)
      throw new Error(data.error || 'Permintaan gagal. Silakan coba lagi.');
    return { ...data, status: response.status };
  };

  // Refresh the server-rendered list and totals together; keep active filters.
  const refreshResults = async (url, focusId) => {
    filterRequest?.abort();
    const controller = new AbortController();
    filterRequest = controller;
    const target = document.querySelector('#audit-results');
    target.setAttribute('aria-busy', 'true');
    const button = target.querySelector('#audit-filter-submit');
    if (button) button.disabled = true;
    try {
      const data = await request(url, { signal: controller.signal });
      if (filterRequest !== controller) return false;
      if (typeof data.html !== 'string') throw new Error('Daftar belum dapat diperbarui.');
      target.innerHTML = data.html;
      target.removeAttribute('data-audit-stale');
      history.replaceState(null, '', url);
      if (focusId) document.getElementById(focusId)?.focus({ preventScroll: true });
      return true;
    } catch (error) {
      if (error.name === 'AbortError') return false;
      throw error;
    } finally {
      if (filterRequest === controller) {
        target.removeAttribute('aria-busy');
        if (button) button.disabled = false;
      }
    }
  };

  const openEntry = async (link) => {
    const dialog = document.querySelector('#audit-dialog');
    if (!dialog?.showModal) return;
    if (document.querySelector('#audit-results')?.hasAttribute('data-audit-stale')) {
      announce('Perbarui riwayat dengan Terapkan atau Reset filter sebelum mengubah catatan lagi.');
      return;
    }
    openingRequest?.abort();
    const controller = new AbortController();
    openingRequest = controller;
    opener = link;
    const content = document.querySelector('#audit-dialog-content');
    content.replaceChildren();
    dialog.removeAttribute('aria-labelledby');
    dialogStatus('Memuat formulir…');
    if (!dialog.open) dialog.showModal();
    document.body.classList.add('audit-dialog-open');
    try {
      const data = await request(link.href, { signal: controller.signal });
      if (!dialog.open || openingRequest !== controller) return;
      if (typeof data.html !== 'string') throw new Error('Formulir belum dapat dimuat.');
      content.innerHTML = data.html;
      const title = content.querySelector('#audit-form-title, #audit-delete-title');
      if (title) dialog.setAttribute('aria-labelledby', title.id);
      dialogStatus('');
      dialog.scrollTop = 0;
      // Confirmation opens on Cancel, keeping destructive actions deliberate.
      (content.querySelector('.audit-delete-panel [data-audit-cancel]')
        || content.querySelector('[name="food_name"]'))?.focus({ preventScroll: true });
    } catch (error) {
      if (error.name !== 'AbortError') dialogStatus(error.message);
    }
  };

  document.addEventListener('close', (event) => {
    if (event.target.id !== 'audit-dialog') return;
    openingRequest?.abort();
    document.body.classList.remove('audit-dialog-open');
    document.querySelector('#audit-dialog-content').replaceChildren();
    dialogStatus('');
    if (opener?.isConnected) opener.focus({ preventScroll: true });
  }, true);
  document.addEventListener('cancel', (event) => {
    if (event.target.id === 'audit-dialog' && mutating) event.preventDefault();
  }, true);

  const returnToHistory = async (url) => {
    // A form opened directly by URL also submits without a document reload.
    const response = await fetch(url, { credentials: 'same-origin' });
    if (response.redirected && new URL(response.url).pathname.includes('/accounts/login/')) {
      location.assign(response.url);
      throw new Error('Sesi berakhir. Silakan masuk kembali.');
    }
    if (!response.ok) throw new Error('Riwayat belum dapat dimuat.');
    const page = new DOMParser().parseFromString(await response.text(), 'text/html');
    const main = page.querySelector('#content.audit-page');
    if (!main?.querySelector('#audit-results')) throw new Error('Riwayat belum dapat dimuat.');
    document.querySelector('#content').innerHTML = main.innerHTML;
    document.title = page.title;
    history.replaceState(null, '', url);
    updateMotion();
    const heading = document.querySelector('.audit-heading h1');
    heading.tabIndex = -1;
    heading.focus();
  };

  const submitEntry = async (form) => {
    if (mutating) return;
    mutating = true;
    filterRequest?.abort();
    const body = new FormData(form);
    const controls = [...form.elements].filter(el => !el.disabled);
    const closeButton = document.querySelector('[data-audit-close]');
    controls.forEach(el => { el.disabled = true; });
    if (closeButton) closeButton.disabled = true;
    form.setAttribute('aria-busy', 'true');
    const inDialog = Boolean(form.closest('#audit-dialog'));
    let changed = false;
    let historyLoaded = false;
    if (inDialog) dialogStatus('Menyimpan perubahan…');
    else announce('Menyimpan perubahan…');
    try {
      const data = await request(form.action, {
        method: 'POST',
        body,
        headers: { 'X-CSRFToken': body.get('csrfmiddlewaretoken') },
      });
      if (data.status === 422) {
        if (typeof data.html !== 'string') throw new Error('Validasi formulir belum dapat ditampilkan.');
        const panel = form.closest('.audit-form-panel');
        if (inDialog) document.querySelector('#audit-dialog-content').innerHTML = data.html;
        else panel.outerHTML = data.html;
        const message = 'Catatan belum tersimpan. Periksa kolom yang ditandai.';
        if (inDialog) dialogStatus(message);
        else announce(message);
        document.querySelector('.audit-field-invalid input, .audit-field-invalid select')?.focus();
        return;
      }
      if (data.ok !== true) throw new Error('Perubahan belum dapat dikonfirmasi.');
      changed = true;
      const results = document.querySelector('#audit-results');
      // A failed refresh must never encourage resubmitting an already saved form.
      if (results) {
        results.setAttribute('data-audit-stale', '');
        results.querySelectorAll('[data-audit-open]').forEach(link => {
          link.setAttribute('aria-disabled', 'true');
        });
        mutating = false;
        document.querySelector('#audit-dialog')?.close();
        historyLoaded = await refreshResults(location.href, 'audit-filter-submit');
        if (historyLoaded) {
          const filter = document.querySelector('[data-audit-filter]');
          const filtered = [...new FormData(filter).values()].some(Boolean);
          announce(data.message + (filtered ? ' Riwayat mengikuti filter yang aktif.' : ''));
        }
      } else {
        await returnToHistory(data.index_url);
        historyLoaded = true;
        announce(data.message);
      }
    } catch (error) {
      const message = changed
        ? 'Perubahan sudah tersimpan, tetapi riwayat belum diperbarui. Gunakan Terapkan, Reset filter, atau kembali ke riwayat.'
        : error instanceof TypeError
          ? 'Koneksi terputus. Periksa riwayat sebelum mencoba menyimpan lagi.'
          : error.message;
      if (inDialog && document.querySelector('#audit-dialog')?.open) dialogStatus(message);
      else announce(message);
    } finally {
      mutating = false;
      form.removeAttribute('aria-busy');
      if (!changed || historyLoaded) controls.forEach(el => { el.disabled = false; });
      if (closeButton) closeButton.disabled = false;
    }
  };

  const searchProducts = async (button) => {
    const form = button.closest('[data-product-target="audit"]');
    const container = form.querySelector('#product-results');
    const query = form.querySelector('#product-query').value.trim();
    if (query.length < 2) {
      container.textContent = 'Masukkan minimal dua karakter.';
      return;
    }
    button.disabled = true;
    container.textContent = 'Mencari produk…';
    const params = new URLSearchParams({
      q: query,
      category: form.querySelector('#product-category').value,
    });
    try {
      const data = await request(button.dataset.auditProductSearch + '?' + params);
      if (!Array.isArray(data.products)) throw new Error('Data produk tidak valid. Isi makanan secara manual.');
      container.replaceChildren();
      const status = document.createElement('p');
      status.textContent = data.products.length ? 'Pilih produk untuk mengisi nama makanan.' : 'Produk tidak ditemukan. Coba kata lain atau isi manual.';
      container.append(status);
      data.products.forEach(product => {
        if (typeof product.name !== 'string') return;
        const choice = document.createElement('button');
        choice.type = 'button';
        choice.className = 'product-result';
        choice.textContent = product.name;
        const category = document.createElement('small');
        category.textContent = typeof product.category === 'string' ? product.category : '';
        choice.append(category);
        choice.addEventListener('click', () => {
          form.elements.food_name.value = product.name;
          form.elements.food_name.focus();
          status.textContent = 'Nama makanan terisi. Lengkapi jumlah, tanggal, alasan, dan perkiraan kerugian.';
        });
        container.append(choice);
      });
    } catch (error) {
      container.textContent = error.message || 'Pencarian gagal. Kamu tetap bisa mengisi makanan secara manual.';
    } finally {
      button.disabled = false;
    }
  };

  document.addEventListener('click', (event) => {
    const motion = event.target.closest('.audit-motion-toggle');
    if (motion) {
      motionPaused = !motionPaused;
      try { localStorage.setItem('audit-motion-paused', String(motionPaused)); } catch {}
      updateMotion();
    }
    const cancel = event.target.closest('[data-audit-close], [data-audit-cancel]');
    if (cancel && document.querySelector('#audit-dialog')?.open) {
      event.preventDefault();
      if (!mutating) document.querySelector('#audit-dialog').close();
    }
    const product = event.target.closest('[data-audit-product-search]');
    if (product) searchProducts(product);
    const link = event.target.closest('[data-audit-open], [data-audit-reset]');
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (link.hasAttribute('data-audit-open')) {
      if (!document.querySelector('#audit-dialog')?.showModal) return;
      event.preventDefault();
      openEntry(link);
    } else {
      event.preventDefault();
      announce('Memperbarui catatan…');
      refreshResults(link.href, 'audit-filter-submit')
        .then(ok => { if (ok) announce('Filter direset. Semua catatan ditampilkan.'); })
        .catch(error => announce(error.message));
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.target.id !== 'product-query' || event.key !== 'Enter' || event.isComposing) return;
    event.preventDefault();
    event.target.closest('form').querySelector('[data-audit-product-search]')?.click();
  });
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (form.matches('[data-audit-mutation]')) {
      event.preventDefault();
      submitEntry(form);
    } else if (form.matches('[data-audit-filter]')) {
      event.preventDefault();
      const url = new URL(form.action);
      url.search = new URLSearchParams(new FormData(form)).toString();
      announce('Memperbarui catatan…');
      refreshResults(url, 'audit-filter-submit')
        .then(ok => {
          if (ok) announce(document.querySelector('.audit-errors')
            ? 'Periksa filter yang dipilih.'
            : 'Riwayat dan ringkasan sudah diperbarui.');
        })
        .catch(error => announce(error.message));
    }
  });
})();

