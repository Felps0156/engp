(() => {
  const dialog = document.querySelector('[data-routine-dialog]');
  if (!dialog) return;

  const openDialog = () => {
    if (!dialog.open) dialog.showModal();
    dialog.querySelector('input:not([type="hidden"])')?.focus();
  };

  document.querySelector('[data-routine-dialog-open]')?.addEventListener(
    'click',
    openDialog,
  );
  dialog.querySelectorAll('[data-routine-dialog-close]').forEach((button) => {
    button.addEventListener('click', () => dialog.close());
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  if (dialog.dataset.open === 'true') openDialog();

  document.querySelectorAll('[data-confirm-delete]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirmDelete)) event.preventDefault();
    });
  });
})();
