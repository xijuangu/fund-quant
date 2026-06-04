const API_BASE = '/api';

async function request<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  get: <T = unknown>(path: string) => request<T>(path),

  post: <T = unknown>(path: string, body: Record<string, unknown>) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),

  put: <T = unknown>(path: string, body: Record<string, unknown>) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),

  del: <T = unknown>(path: string) =>
    request<T>(path, { method: 'DELETE' }),
};

export default api;
