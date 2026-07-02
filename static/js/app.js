(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('#theme-toggle');
  const savedTheme = localStorage.getItem('ihis-theme');
  if (savedTheme) root.setAttribute('data-bs-theme', savedTheme);
  const updateIcon = () => {
    if (!toggle) return;
    const dark = root.getAttribute('data-bs-theme') === 'dark';
    toggle.innerHTML = `<i class="bi bi-${dark ? 'sun' : 'moon-stars'}"></i>`;
  };
  updateIcon();
  toggle?.addEventListener('click', () => {
    const next = root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-bs-theme', next);
    localStorage.setItem('ihis-theme', next);
    updateIcon();
  });
  document.querySelectorAll('[data-password-target]').forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.passwordTarget);
      if (!input) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      button.setAttribute('aria-label', input.type === 'password' ? 'Show password' : 'Hide password');
    });
  });
})();
