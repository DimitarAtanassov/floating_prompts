/**
 * Connection settings (API base URL) persisted in localStorage.
 *
 * A tiny pub/sub lets React components re-render when settings change, without
 * pulling in a state library.
 */

const BASE_URL_KEY = "fp.baseUrl"

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000"

type Listener = () => void
const listeners = new Set<Listener>()

export function getBaseUrl(): string {
  return localStorage.getItem(BASE_URL_KEY) ?? DEFAULT_BASE_URL
}

export function setSettings(next: { baseUrl: string }): void {
  localStorage.setItem(BASE_URL_KEY, next.baseUrl.replace(/\/$/, ""))
  for (const listener of listeners) listener()
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
