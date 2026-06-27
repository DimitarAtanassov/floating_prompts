/**
 * Type-safe API client built on openapi-fetch, typed by the generated schema.
 *
 * The client is rebuilt when the base URL changes. `ApiError` normalizes the
 * service's RFC 9457 problem responses.
 */

import createClient from "openapi-fetch"
import { getBaseUrl, subscribe } from "@/lib/settings"
import type { components, paths } from "./schema"

export type Schemas = components["schemas"]

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly extra: Record<string, unknown>

  constructor(
    message: string,
    status: number,
    code: string,
    extra: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
    this.extra = extra
  }
}

function build() {
  return createClient<paths>({ baseUrl: getBaseUrl() })
}

let client = build()
subscribe(() => {
  client = build()
})

/** The current typed API client. */
export function api() {
  return client
}

type Problem = {
  detail?: string
  title?: string
  code?: string
  extra?: Record<string, unknown>
}

/**
 * Unwrap an openapi-fetch result: return data on success, throw `ApiError`
 * (parsed from problem+json) otherwise.
 */
export function unwrap<T>(result: {
  data?: T
  error?: unknown
  response: Response
}): T {
  if (result.error !== undefined || !result.response.ok) {
    const p = (result.error ?? {}) as Problem
    throw new ApiError(
      p.detail ?? p.title ?? `Request failed (${result.response.status})`,
      result.response.status,
      p.code ?? "error",
      p.extra ?? {},
    )
  }
  return result.data as T
}
