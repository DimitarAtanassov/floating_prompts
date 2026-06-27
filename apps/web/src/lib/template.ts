/** Detect `{{ variable }}` names referenced in templates (mirrors the server). */
export function detectVariables(...templates: (string | null | undefined)[]): string[] {
  const pattern = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g
  const found = new Set<string>()
  for (const template of templates) {
    if (!template) continue
    for (const match of template.matchAll(pattern)) {
      found.add(match[1])
    }
  }
  return [...found].sort()
}
