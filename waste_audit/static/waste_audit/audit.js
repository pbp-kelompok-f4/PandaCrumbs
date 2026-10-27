(() => {
  if (!document.body.classList.contains('audit-body')) return;
  const motionButton = document.querySelector('.audit-motion-toggle');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let motionPaused = false;
  try { motionPaused = localStorage.getItem('audit-motion-paused') === 'true'; } catch {}
  const updateMotion = () => {
    document.body.classList.toggle('audit-motion-paused', motionPaused);
    motionButton.hidden = reducedMotion.matches;
    motionButton.setAttribute('aria-pressed', String(motionPaused));
    motionButton.textContent = motionPaused ? 'Lanjutkan animasi latar' : 'Jeda animasi latar';
  };
  motionButton.addEventListener('click', () => {
    motionPaused = !motionPaused;
    try { localStorage.setItem('audit-motion-paused', String(motionPaused)); } catch {}
    updateMotion();
  });
  reducedMotion.addEventListener('change', updateMotion);
  updateMotion();
  // Product lookup is optional and must not submit the audit form on Enter.
  document.querySelector('#product-query')?.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' || event.isComposing) return;
    event.preventDefault();
    document.querySelector('[data-product-search]')?.click();
  });
  let activeRequest;
  document.addEventListener('submit', async (event) => {
    const form = event.target.closest('[data-audit-filter]');
    if (!form) return;
    event.preventDefault();
    activeRequest?.abort();
    const controller = new AbortController();
    activeRequest = controller;
    const target = document.querySelector('#audit-results');
    const status = document.querySelector('#audit-filter-status');
    const button = form.querySelector('[type="submit"]');
    const focusId = document.activeElement?.id || 'audit-filter-submit';
    const url = new URL(form.action, location.origin);
    url.search = new URLSearchParams(new FormData(form)).toString();
    target.setAttribute('aria-busy', 'true');
    button.disabled = true;
    status.textContent = 'Memperbarui catatan…';
    try {
      const response = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: controller.signal,
      });
      if (response.redirected && new URL(response.url).pathname.includes('/accounts/login/')) {
        location.assign(response.url);
        return;
      }
      if (!response.ok) throw new Error('Catatan belum dapat diperbarui. Silakan coba lagi.');
      const data = await response.json();
      if (typeof data.html !== 'string') throw new Error('Respons tidak valid. Silakan muat ulang halaman.');
      if (activeRequest !== controller) return;
      target.innerHTML = data.html;
      history.replaceState(null, '', url);
      status.textContent = target.querySelector('.audit-errors')
        ? 'Filter belum diterapkan. Periksa tanggal dan alasan yang dipilih.'
        : 'Riwayat dan ringkasan sudah diperbarui.';
      document.getElementById(focusId)?.focus({ preventScroll: true });
    } catch (error) {
      if (error.name !== 'AbortError' && activeRequest === controller)
        status.textContent = error.message || 'Koneksi terputus. Silakan coba lagi.';
    } finally {
      if (activeRequest === controller) {
        target.removeAttribute('aria-busy');
        button.disabled = false;
      }
    }
  });
})();
