import { writable } from 'svelte/store';

export const user = writable(null);
export const loading = writable(false);
export const capaNBIActiva = writable(false);

// Rutas relativas → van por el proxy de Vite (vite.config.ts server.proxy)
export async function fetchAPI(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function checkAuth() {
  try {
    const data = await fetchAPI('/api/auth/me/');
    user.set(data);
    return data;
  } catch {
    user.set(null);
    return null;
  }
}

export async function login(username, password) {
  const data = await fetchAPI('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  user.set(data);
  return data;
}

export async function logout() {
  await fetchAPI('/api/auth/logout/');
  user.set(null);
}
