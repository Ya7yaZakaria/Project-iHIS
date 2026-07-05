(() => {
  const root = document.documentElement;
  const collapse = document.querySelector('#sidebar-collapse');
  const collapsed = localStorage.getItem('ihis-sidebar-collapsed') === 'true';
  if (collapsed) root.classList.add('sidebar-collapsed');
  collapse?.addEventListener('click', () => {
    root.classList.toggle('sidebar-collapsed');
    localStorage.setItem('ihis-sidebar-collapsed', root.classList.contains('sidebar-collapsed'));
  });

  document.querySelectorAll('[data-table-filter]').forEach((input) => input.addEventListener('input', () => {
    const table = input.closest('.card')?.querySelector('[data-dashboard-table]');
    const term = input.value.trim().toLowerCase();
    table?.querySelectorAll('tbody tr:not(.empty-row)').forEach((row) => {
      row.classList.toggle('d-none', !row.textContent.toLowerCase().includes(term));
    });
  }));

  document.querySelectorAll('[data-widget-refresh]').forEach((button) => button.addEventListener('click', () => {
    const icon = button.querySelector('i');
    icon?.classList.add('spin-once');
    button.disabled = true;
    button.lastChild.textContent = ' Refresh queued';
    window.setTimeout(() => { button.disabled = false; button.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh'; }, 800);
  }));

  let pendingForm = null;
  document.querySelectorAll('[data-confirm]').forEach((trigger) => trigger.addEventListener('click', (event) => {
    event.preventDefault(); pendingForm = trigger.closest('form');
    const modal = document.querySelector('#confirmationModal');
    if (modal) {
      modal.querySelector('[data-confirmation-message]').textContent = trigger.dataset.confirm || 'Are you sure?';
      bootstrap.Modal.getOrCreateInstance(modal).show();
    }
  }));
  document.querySelector('[data-confirmation-submit]')?.addEventListener('click', () => pendingForm?.submit());

  document.querySelectorAll('form[data-validate]').forEach((form) => form.addEventListener('submit', (event) => {
    if (!form.checkValidity()) { event.preventDefault(); event.stopPropagation(); }
    form.classList.add('was-validated');
  }));

  document.querySelectorAll('[data-chart-placeholder]').forEach((canvas) => {
    if (!window.Chart) return;
    new Chart(canvas, {type: 'bar', data: {labels: [], datasets: [{data: []}]}, options: {responsive: true}});
  });
})();
