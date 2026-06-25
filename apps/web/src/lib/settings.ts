/**
 * Connection settings (API base URL + API key) persisted in localStorage.
 *
 * A tiny pub/sub lets React components re-render when settings change, without
 * pulling in a state library for two values.
 */

const BASE_URL_KEY = "fp.baseUrl"
const API_KEY_KEY = "fp.apiKey"

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000"

type Listener = () => void
const listeners = new Set<Listener>()

export function getBaseUrl(): string {
  return localStorage.getItem(BASE_URL_KEY) ?? DEFAULT_BASE_URL
}

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_KEY) ?? ""
}

export function setSettings(next: { baseUrl: string; apiKey: string }): void {
  localStorage.setItem(BASE_URL_KEY, next.baseUrl.replace(/\/$/, ""))
  localStorage.setItem(API_KEY_KEY, next.apiKey.trim())
  for (const listener of listeners) listener()
}

export function hasApiKey(): boolean {
  return getApiKey().length > 0
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
