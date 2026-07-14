import { supabase } from '../lib/supabaseClient';
import { ApiError } from './errors';

// Empty string -> same-origin relative '/api/...' requests, which the Vite
// dev server proxies to a local FastAPI instance (see vite.config.ts).
// Set VITE_API_BASE_URL to the deployed Render URL for production builds
// (the two apps are no longer same-origin now that the backend moved off
// Cloudflare Workers static-assets hosting).
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

export const api = {
  async request<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
    // Supabase's client manages token refresh internally; grabbing the
    // session here (rather than reading a manually-stored token) always
    // gets a currently-valid access token, refreshing it first if needed.
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    const headers = new Headers(options.headers || {});

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_BASE_URL}/api${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const responseText = await response.text();
      let errInfo: Record<string, unknown>;
      try {
        const parsed: unknown = responseText ? JSON.parse(responseText) : {};
        errInfo = parsed && typeof parsed === 'object' && !Array.isArray(parsed)
          ? parsed as Record<string, unknown>
          : { message: responseText };
      } catch {
        errInfo = { message: responseText };
      }
      const message = typeof errInfo.message === 'string'
        ? errInfo.message
        : typeof errInfo.error === 'string' ? errInfo.error : 'Request failure.';
      throw new ApiError(
        message,
        response.status,
        errInfo
      );
    }

    if (response.status === 204) {
      return null as T;
    }

    const data2 = await response.json();
    return data2 as T;
  },

  get<T = unknown>(path: string, options?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' });
  },

  post<T = unknown>(path: string, body: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },

  put<T = unknown>(path: string, body: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  patch<T = unknown>(path: string, body: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },

  delete<T = unknown>(path: string, options?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' });
  },
};
