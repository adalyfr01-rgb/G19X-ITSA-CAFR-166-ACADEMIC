const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiFetch(ruta, opciones = {}) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(opciones.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
  return fetch(`${API_URL}${ruta}`, { ...opciones, headers });
}