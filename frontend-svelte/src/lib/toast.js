import { writable } from 'svelte/store';

// Cola global de notificaciones (toasts)
export const toasts = writable([]);

let _id = 0;

function show(type, message, timeout = 3800) {
  const id = ++_id;
  toasts.update(list => [...list, { id, type, message }]);
  if (timeout) setTimeout(() => dismiss(id), timeout);
  return id;
}

export function dismiss(id) {
  toasts.update(list => list.filter(t => t.id !== id));
}

export const toast = {
  success: (m, t) => show('success', m, t),
  error:   (m, t) => show('error', m, t ?? 5000),
  info:    (m, t) => show('info', m, t),
  warning: (m, t) => show('warning', m, t),
};
