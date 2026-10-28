(() => {
  const dashboard = document.querySelector('#habit-dashboard');
  const checkinDialog = document.querySelector('#habit-checkin-dialog');
  const successDialog = document.querySelector('#habit-success-dialog');
  let activeForm = null;
  let formHome = null;
  let returnFocus = null;

  const focusDashboard = () => {
    const title = dashboard?.querySelector('.habit-title');
    title?.setAttribute('tabindex', '-1');
    title?.focus({ preventScroll: true });
  };
  const openCheckin = (details) => {
    if (!checkinDialog?.showModal || checkinDialog.open) return;
    activeForm = details.querySelector('[data-habit-checkin]');
    if (!activeForm) return;
    formHome = details;
    returnFocus = details.querySelector('summary');
    details.open = false;
    document.querySelector('#habit-checkin-description').textContent = details.dataset.challengeTitle;
    document.querySelector('#habit-dialog-form').append(activeForm);
    checkinDialog.showModal();
    document.body.classList.add('habit-modal-open');
    activeForm.elements.food.focus();
  };
  dashboard?.addEventListener('click', (event) => {
    const summary = event.target.closest('.habit-checkin > summary');
    if (!summary || !checkinDialog?.showModal) return;
    event.preventDefault();
    openCheckin(summary.parentElement);
  });
  checkinDialog?.addEventListener('close', () => {
    if (activeForm && formHome?.isConnected) formHome.append(activeForm);
    activeForm = null;
    formHome = null;
    if (!successDialog?.open) {
      document.body.classList.remove('habit-modal-open');
      if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
      else focusDashboard();
    }
  });
  successDialog?.addEventListener('close', () => {
    document.body.classList.remove('habit-modal-open');
    focusDashboard();
  });
  [checkinDialog, successDialog].forEach(dialog => {
    dialog?.addEventListener('click', event => {
      if (event.target.closest('[data-close-dialog]')) dialog.close();
    });
    // Keep the form visible until the server answers, including on Escape.
    dialog?.addEventListener('cancel', event => {
      if (dialog.getAttribute('aria-busy') === 'true') event.preventDefault();
    });
  });
  const invalidDetails = dashboard?.querySelector('.habit-checkin[open]');
  if (invalidDetails) openCheckin(invalidDetails);

  const submitCheckin = async (event) => {
    const form = event.target.closest('[data-habit-checkin]');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    if (button.disabled) return;
    const errors = form.querySelector('.habit-form-errors');
    const body = new FormData(form);
    button.disabled = true;
    if (checkinDialog?.open) {
      checkinDialog.setAttribute('aria-busy', 'true');
      checkinDialog.querySelector('[data-close-dialog]').disabled = true;
    }
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
      const completion = data.completion;
      if (checkinDialog?.open) {
        // Return the form before replacing its original card.
        if (formHome?.isConnected) formHome.append(form);
        activeForm = null;
        checkinDialog.close();
      }
      // This is escaped HTML rendered by our Django template, never an upstream API.
      dashboard.innerHTML = data.html;
      if (successDialog?.showModal && completion) {
        document.querySelector('#habit-success-title').textContent = completion.created
          ? 'Poin berhasil ditambahkan!' : 'Tantangan sudah tercatat';
        document.querySelector('#habit-success-food').textContent = completion.created
          ? `${completion.food} berhasil ${completion.action}` : completion.food;
        document.querySelector('#habit-success-reward').textContent = completion.created
          ? `+${completion.points} poin ${completion.reward}`
          : 'Poin hari ini sudah diterima. Yuk, kembali besok!';
        successDialog.showModal();
        document.body.classList.add('habit-modal-open');
      } else {
        const feedback = document.querySelector('#feedback');
        feedback.textContent = data.message;
        feedback.hidden = false;
        focusDashboard();
        setTimeout(() => { feedback.hidden = true; }, 6000);
      }
    } catch (error) {
      errors.textContent = error.message || 'Koneksi terputus. Coba lagi.';
      errors.setAttribute('tabindex', '-1');
      errors.focus();
    } finally {
      button.disabled = false;
      checkinDialog?.removeAttribute('aria-busy');
      if (checkinDialog) checkinDialog.querySelector('[data-close-dialog]').disabled = false;
    }
  };
  dashboard?.addEventListener('submit', submitCheckin);
  checkinDialog?.addEventListener('submit', submitCheckin);

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
