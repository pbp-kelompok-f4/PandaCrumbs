(() => {
  const toast = (message) => {
    const box = document.querySelector('#feedback');
    box.textContent = message;
    box.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => { box.hidden = true; }, 6000);
  };
  const request = async (url, options = {}) => {
    const response = await fetch(url, { ...options, headers: { 'X-Requested-With': 'XMLHttpRequest', ...options.headers } });
    if (response.redirected && new URL(response.url).pathname.includes('/accounts/login/')) {
      window.location.assign(response.url);
      throw new Error('Sesi berakhir. Silakan masuk kembali.');
    }
    const data = await response.json().catch(() => { throw new Error('Respons tidak valid. Muat ulang halaman dan coba lagi.'); });
    if (!response.ok) throw new Error(data.error || 'Perubahan gagal disimpan. Coba lagi.');
    return data;
  };
  const menu = document.querySelector('.menu-toggle');
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    document.querySelector('#site-navigation').classList.toggle('open', open);
  });
  const filter = document.querySelector('[data-filter-form]');
  let activeRequest;
  const renderIngredients = (params) => {
    const container = document.querySelector('#active-ingredients');
    if (!container) return;
    container.replaceChildren();
    [...new Set(params.getAll('ingredient'))].forEach(value => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'pill selected'; button.dataset.removeIngredient = value;
      button.append(document.createTextNode(value + ' '));
      const icon = document.createElement('img');
      icon.src = '/static/main/images/recipeDesign-imgButtonHapusNasi.svg'; icon.alt = 'Hapus';
      const hidden = document.createElement('input');
      hidden.type = 'hidden'; hidden.name = 'ingredient'; hidden.value = value;
      button.append(icon, hidden); container.append(button);
    });
  };
  const refresh = async (params, updateHistory = true) => {
    if (!filter) return;
    activeRequest?.abort();
    activeRequest = new AbortController();
    const target = document.getElementById(filter.dataset.target);
    target.setAttribute('aria-busy', 'true');
    const url = new URL(window.location.pathname, window.location.origin);
    url.search = params.toString();
    try {
      const data = await request(url, { signal: activeRequest.signal });
      target.innerHTML = data.html;
      if (updateHistory) history.replaceState(null, '', url);
      filter.querySelectorAll('[name=status]').forEach(b => b.classList.toggle('selected', b.value === (params.get('status') || '')));
      if (filter.elements.tab) filter.elements.tab.value = params.get('tab') || 'all';
      renderIngredients(params);
    } catch (error) {
      if (error.name !== 'AbortError') toast(error.message);
    } finally { target.removeAttribute('aria-busy'); }
  };
  filter?.addEventListener('submit', event => {
    event.preventDefault();
    const params = new URLSearchParams(new FormData(filter));
    const submitter = event.submitter;
    if (submitter?.name === 'ingredient') {
      if (!params.getAll('ingredient').includes(submitter.value)) params.append('ingredient', submitter.value);
    } else if (submitter?.name) params.set(submitter.name, submitter.value);
    if (filter.querySelector('[name=status]') && submitter?.name !== 'status') {
      params.set('status', new URLSearchParams(location.search).get('status') || '');
    }
    refresh(params);
  });
  document.querySelectorAll('[data-auto-submit]').forEach(element => element.addEventListener('change', () => filter.requestSubmit()));
  document.addEventListener('click', event => {
    const remove = event.target.closest('[data-remove-ingredient]');
    const reset = event.target.closest('[data-reset-ingredients]');
    const tab = event.target.closest('[data-tab]');
    if (!filter || (!remove && !reset && !tab)) return;
    event.preventDefault();
    const params = new URLSearchParams(new FormData(filter));
    if (remove) {
      const remaining = params.getAll('ingredient').filter(value => value !== remove.dataset.removeIngredient);
      params.delete('ingredient'); remaining.forEach(value => params.append('ingredient', value));
    }
    if (reset) params.delete('ingredient');
    if (tab) params.set('tab', tab.dataset.tab);
    refresh(params);
  });
  document.addEventListener('submit', async event => {
    const form = event.target.closest('[data-action]');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('button');
    if (button.disabled) return;
    button.disabled = true;
    try {
      const data = await request(form.action, { method: 'POST', body: new FormData(form) });
      if (filter) await refresh(new URLSearchParams(location.search), false);
      else if (form.dataset.action === 'bookmark') {
        form.elements.saved.value = data.saved ? '0' : '1';
        button.setAttribute('aria-pressed', String(data.saved));
        button.setAttribute('aria-label', data.saved ? 'Hapus bookmark' : 'Simpan resep');
        button.replaceChildren();
        const img = document.createElement('img');
        img.src = '/static/main/images/recipeDesign-imgContainer' + (data.saved ? '1' : '2') + '.svg'; img.alt = '';
        button.append(img, document.createTextNode(data.saved ? 'Tersimpan' : 'Simpan'));
      }
      toast(form.dataset.action === 'consume' ? 'Stok dikurangi. Bahan dengan stok nol otomatis dihapus.' : (data.saved ? 'Resep disimpan.' : 'Bookmark dihapus.'));
    } catch (error) { toast(error.message); }
    finally { button.disabled = false; }
  });
  document.querySelector('[data-product-search]')?.addEventListener('click', async event => {
    const button = event.currentTarget;
    const container = document.querySelector('#product-results');
    const query = document.querySelector('#product-query').value.trim();
    if (query.length < 2) { container.textContent = 'Masukkan minimal dua karakter.'; return; }
    button.disabled = true; container.textContent = 'Mencari produk…';
    const params = new URLSearchParams({ q: query, category: document.querySelector('#product-category').value.trim() });
    try {
      const data = await request(button.dataset.productSearch + '?' + params);
      container.replaceChildren();
      if (!data.products.length) container.textContent = 'Produk tidak ditemukan. Coba kata lain atau isi manual.';
      data.products.forEach(product => {
        const choice = document.createElement('button');
        choice.type = 'button'; choice.className = 'product-result';
        choice.textContent = product.name;
        const category = document.createElement('small'); category.textContent = product.category; choice.append(category);
        choice.addEventListener('click', () => {
          const form = document.querySelector('[data-product-target]');
          if (form.dataset.productTarget === 'pantry') {
            form.elements.name.value = product.name;
            form.elements.barcode.value = product.barcode;
            form.elements.image_url.value = typeof product.image === 'string' && product.image.startsWith('https://') ? product.image : '';
          } else {
            form.elements.ingredients.value += (form.elements.ingredients.value ? '\n' : '') + product.name;
          }
          toast('Produk dipilih. Lengkapi takaran, kategori, dan tanggal secara manual.');
        });
        container.append(choice);
      });
    } catch (error) { container.textContent = error.message; }
    finally { button.disabled = false; }
  });
  document.addEventListener('error', event => {
    if (event.target.tagName === 'IMG' && event.target.closest('.pantry-photo,.recipe-photo,.detail-photo')) {
      const fallback = document.createElement('div'); fallback.className = 'no-photo'; fallback.textContent = 'Foto tidak tersedia';
      event.target.replaceWith(fallback);
    }
  }, true);
})();
