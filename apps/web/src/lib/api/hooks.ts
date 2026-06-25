/**
 * TanStack Query hooks over the typed API client. Queries read; mutations write
 * and invalidate the affected queries so the UI stays consistent.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { getApiKey, getBaseUrl } from "@/lib/settings"
import { api, unwrap } from "./client"
import type {
  ApiKeyCreate,
  ApiKeyCreated,
  PromptVersionCreate,
  RenderResult,
} from "./models"

export const keys = {
  projects: ["projects"] as const,
  project: (slug: string) => ["project", slug] as const,
  prompts: (slug: string) => ["prompts", slug] as const,
  prompt: (slug: string, name: string) => ["prompt", slug, name] as const,
  versions: (slug: string, name: string) => ["versions", slug, name] as const,
  tags: (slug: string, name: string) => ["tags", slug, name] as const,
  apiKeys: (slug: string) => ["apiKeys", slug] as const,
}

// -- Connection -------------------------------------------------------------

export type Health = { ok: boolean; database?: string; keySet: boolean }

export function useHealth() {
  return useQuery<Health>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await fetch(`${getBaseUrl()}/readyz`)
      const body = (await res.json().catch(() => ({}))) as {
        status?: string
        database?: string
      }
      return {
        ok: res.ok && body.status === "ok",
        database: body.database,
        keySet: getApiKey().length > 0,
      }
    },
    refetchInterval: 15_000,
    retry: false,
  })
}

// -- Projects ---------------------------------------------------------------

export function useProjects() {
  return useQuery({
    queryKey: keys.projects,
    queryFn: async () =>
      unwrap(await api().GET("/api/v1/projects", { params: { query: {} } }))
        .items,
  })
}

export function useProject(slug: string) {
  return useQuery({
    queryKey: keys.project(slug),
    queryFn: async () =>
      unwrap(
        await api().GET("/api/v1/projects/{slug}", {
          params: { path: { slug } },
        }),
      ),
    enabled: slug.length > 0,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { slug: string; name: string; description?: string | null }) =>
      unwrap(await api().POST("/api/v1/projects", { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.projects }),
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (slug: string) =>
      unwrap(
        await api().DELETE("/api/v1/projects/{slug}", {
          params: { path: { slug } },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.projects }),
  })
}

// -- Prompts ----------------------------------------------------------------

export function usePrompts(slug: string) {
  return useQuery({
    queryKey: keys.prompts(slug),
    queryFn: async () =>
      unwrap(
        await api().GET("/api/v1/projects/{slug}/prompts", {
          params: { path: { slug }, query: {} },
        }),
      ).items,
    enabled: slug.length > 0,
  })
}

export function useCreatePrompt(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { name: string; description?: string | null }) =>
      unwrap(
        await api().POST("/api/v1/projects/{slug}/prompts", {
          params: { path: { slug } },
          body,
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.prompts(slug) }),
  })
}

export function useDeletePrompt(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (name: string) =>
      unwrap(
        await api().DELETE("/api/v1/projects/{slug}/prompts/{name}", {
          params: { path: { slug, name } },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.prompts(slug) }),
  })
}

// -- Versions ---------------------------------------------------------------

export function useVersions(slug: string, name: string) {
  return useQuery({
    queryKey: keys.versions(slug, name),
    queryFn: async () =>
      unwrap(
        await api().GET("/api/v1/projects/{slug}/prompts/{name}/versions", {
          params: { path: { slug, name } },
        }),
      ),
    enabled: slug.length > 0 && name.length > 0,
  })
}

export function useCreateVersion(slug: string, name: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: PromptVersionCreate) =>
      unwrap(
        await api().POST(
          "/api/v1/projects/{slug}/prompts/{name}/versions",
          { params: { path: { slug, name } }, body },
        ),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.versions(slug, name) })
      qc.invalidateQueries({ queryKey: keys.tags(slug, name) })
    },
  })
}

// -- Tags -------------------------------------------------------------------

export function useTags(slug: string, name: string) {
  return useQuery({
    queryKey: keys.tags(slug, name),
    queryFn: async () =>
      unwrap(
        await api().GET("/api/v1/projects/{slug}/prompts/{name}/tags", {
          params: { path: { slug, name } },
        }),
      ),
    enabled: slug.length > 0 && name.length > 0,
  })
}

export function useSetTag(slug: string, name: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (vars: { tag: string; version: number }) =>
      unwrap(
        await api().PUT(
          "/api/v1/projects/{slug}/prompts/{name}/tags/{tag_name}",
          {
            params: { path: { slug, name, tag_name: vars.tag } },
            body: { version: vars.version },
          },
        ),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.tags(slug, name) }),
  })
}

export function useDeleteTag(slug: string, name: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (tag: string) =>
      unwrap(
        await api().DELETE(
          "/api/v1/projects/{slug}/prompts/{name}/tags/{tag_name}",
          { params: { path: { slug, name, tag_name: tag } } },
        ),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.tags(slug, name) }),
  })
}

// -- Render -----------------------------------------------------------------

export function useRender(slug: string, name: string) {
  return useMutation<
    RenderResult,
    Error,
    { variables: Record<string, unknown>; version?: number | null; tag?: string | null }
  >({
    mutationFn: async (body) =>
      unwrap(
        await api().POST(
          "/api/v1/projects/{slug}/prompts/{name}/render",
          { params: { path: { slug, name } }, body },
        ),
      ),
  })
}

// -- API keys ---------------------------------------------------------------

export function useApiKeys(slug: string) {
  return useQuery({
    queryKey: keys.apiKeys(slug),
    queryFn: async () =>
      unwrap(
        await api().GET("/api/v1/projects/{slug}/api-keys", {
          params: { path: { slug } },
        }),
      ),
    enabled: slug.length > 0,
  })
}

export function useIssueApiKey(slug: string) {
  const qc = useQueryClient()
  return useMutation<ApiKeyCreated, Error, ApiKeyCreate>({
    mutationFn: async (body) =>
      unwrap(await api().POST("/api/v1/api-keys", { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.apiKeys(slug) }),
  })
}

export function useRevokeApiKey(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (keyId: number) =>
      unwrap(
        await api().DELETE("/api/v1/api-keys/{key_id}", {
          params: { path: { key_id: keyId } },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.apiKeys(slug) }),
  })
}
