(() => {
  const dashboard = document.querySelector('#habit-dashboard');
  dashboard?.addEventListener('submit', async (event) => {
    const form = event.target.closest('[data-habit-checkin]');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const errors = form.querySelector('.habit-form-errors');
    const body = new FormData(form);
    button.disabled = true;
    errors.textContent = '';
    try {
      const response = await fetch(form.action, {
        method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (response.redirected) {
        window.location.assign(response.url);
        return;
      }
      const data = await response.json();
      if (!response.ok) {
        const messages = Object.values(data.errors || {}).flat().map(error => error.message);
        throw new Error(messages.join(' ') || 'Catatan belum tersimpan. Coba lagi.');
      }
      // This is escaped HTML rendered by our Django template, never an upstream API.
      dashboard.innerHTML = data.html;
      const feedback = document.querySelector('#feedback');
      feedback.textContent = data.message;
      feedback.hidden = false;
      dashboard.querySelector('.habit-title').setAttribute('tabindex', '-1');
      dashboard.querySelector('.habit-title').focus({ preventScroll: true });
      setTimeout(() => { feedback.hidden = true; }, 6000);
    } catch (error) {
      errors.textContent = error.message || 'Koneksi terputus. Coba lagi.';
    } finally {
      button.disabled = false;
    }
  });

  const search = document.querySelector('#habit-product-search');
  search?.addEventListener('click', async () => {
    const results = document.querySelector('#habit-product-results');
    const form = document.querySelector('#habit-plan-form');
    const query = document.querySelector('#habit-product-query').value.trim();
    if (query.length < 2) {
      results.textContent = 'Masukkan minimal dua karakter.';
      return;
    }
    search.disabled = true;
    results.textContent = 'Mencari produk…';
    try {
      const params = new URLSearchParams({ q: query, category: form.elements.category.value });
      const response = await fetch(`${search.dataset.url}?${params}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (response.redirected) {
        window.location.assign(response.url);
        return;
      }
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Pencarian gagal. Isi bahan secara manual.');
      results.replaceChildren();
      if (!data.products.length) results.textContent = 'Produk tidak ditemukan. Coba nama lain atau isi bahan secara manual.';
      data.products.forEach(product => {
        const choice = document.createElement('button');
        choice.type = 'button';
        choice.className = 'product-result';
        choice.textContent = product.name;
        choice.addEventListener('click', () => {
          form.elements.food.value = product.name;
          form.elements.food.focus();
          results.textContent = `Bahan sasaran dipilih: ${product.name}`;
        });
        results.append(choice);
      });
    } catch (error) {
      results.textContent = error.message || 'Pencarian gagal. Isi bahan secara manual.';
    } finally {
      search.disabled = false;
    }
  });
})();
