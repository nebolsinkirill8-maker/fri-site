(() => {
  const input = document.getElementById('id_photo');
  if (!input) return;
  const preview = document.getElementById('photo-preview');
  const placeholder = document.getElementById('photo-placeholder');
  const error = document.getElementById('photo-error');
  const state = document.getElementById('photo-state');
  const initial = preview.getAttribute('src');
  let url;
  input.addEventListener('change', () => {
    if (url) URL.revokeObjectURL(url);
    const file = input.files[0];
    error.textContent = '';
    if (!file) { preview.hidden = !initial; if(initial) preview.src = initial; placeholder.hidden = !!initial; return; }
    if (file.size > 10 * 1024 * 1024 || !['image/jpeg','image/png','image/webp'].includes(file.type)) {
      input.value = ''; error.textContent = 'Выбери JPG, PNG или WebP до 10 МБ.'; preview.hidden = !initial; if(initial) preview.src = initial; placeholder.hidden = !!initial; return;
    }
    url = URL.createObjectURL(file); preview.src = url; preview.hidden = false; placeholder.hidden = true;
    const clear = document.getElementById('photo-clear_id'); if(clear) clear.checked = false;
    state.textContent = 'Фото выбрано. Сохрани профиль, чтобы применить изменения.';
  });
})();
