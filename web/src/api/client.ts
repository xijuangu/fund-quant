const API_BASE = '/api';

function parseErrorMessage(text: string, fallback: string): string {
  if (!text) return fallback;
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === 'string') {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item) => item.msg || JSON.stringify(item)).join('; ');
    }
  } catch {
    return text;
  }
  return text;
}

async function request<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseErrorMessage(text, res.statusText));
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
