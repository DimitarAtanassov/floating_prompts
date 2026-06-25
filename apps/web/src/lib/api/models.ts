/** Friendly aliases for the generated API schema types. */

import type { Schemas } from "./client"

export type Project = Schemas["ProjectRead"]
export type ProjectCreate = Schemas["ProjectCreate"]
export type Prompt = Schemas["PromptRead"]
export type PromptCreate = Schemas["PromptCreate"]
export type PromptVersion = Schemas["PromptVersionRead"]
export type PromptVersionCreate = Schemas["PromptVersionCreate"]
export type VariableSpec = Schemas["VariableSpec"]
export type Tag = Schemas["TagRead"]
export type RenderResult = Schemas["RenderResult"]
export type ApiKey = Schemas["ApiKeyRead"]
export type ApiKeyCreate = Schemas["ApiKeyCreate"]
export type ApiKeyCreated = Schemas["ApiKeyCreated"]

export type Scope = ApiKeyCreate["scopes"][number]
export const SCOPES: Scope[] = ["read", "write", "admin"]
