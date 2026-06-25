import { AnimatePresence, motion } from "motion/react"
import { Sparkles, Wand2 } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { CopyButton } from "@/components/copy-button"
import { EmptyState } from "@/components/empty-state"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import {
  useProjects,
  usePrompts,
  useRender,
  useTags,
  useVersions,
} from "@/lib/api/hooks"
import { easeOut } from "@/lib/motion"

export function PlaygroundPage() {
  const [params, setParams] = useSearchParams()
  const project = params.get("project") ?? ""
  const prompt = params.get("prompt") ?? ""

  const projects = useProjects()
  const prompts = usePrompts(project)
  const { data: versions } = useVersions(project, prompt)
  const { data: tags } = useTags(project, prompt)
  const render = useRender(project, prompt)

  const [target, setTarget] = useState<string>("")
  const [values, setValues] = useState<Record<string, string>>({})

  // Default the target to the latest version when versions load.
  useEffect(() => {
    if (versions && versions.length > 0) {
      setTarget((curr) => curr || `ver:${versions[0].version}`)
    }
  }, [versions])

  // The version object the current target points at (for its variable list).
  const selected = useMemo(() => {
    if (!versions) return undefined
    if (target.startsWith("ver:")) {
      return versions.find((v) => v.version === Number(target.slice(4)))
    }
    if (target.startsWith("tag:")) {
      const tag = tags?.find((t) => t.name === target.slice(4))
      return versions.find((v) => v.id === tag?.version_id)
    }
    return undefined
  }, [target, versions, tags])

  const variables = selected?.variables ?? []

  function setField(name: string, value: string) {
    setValues((v) => ({ ...v, [name]: value }))
  }

  async function run() {
    const payload = target.startsWith("tag:")
      ? { variables: values, tag: target.slice(4) }
      : { variables: values, version: Number(target.slice(4)) }
    try {
      await render.mutateAsync(payload)
    } catch (err) {
      // ApiError messages (e.g. missing variables) surface here.
      toast.error(err instanceof Error ? err.message : "Render failed")
    }
  }

  const ready = project && prompt && selected

  return (
    <div className="space-y-6">
      <PageHeader
        title="Playground"
        description="Render a prompt with live variable values."
      />

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label>Project</Label>
          <Select
            value={project}
            onValueChange={(v) => setParams({ project: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {projects.data?.map((p) => (
                <SelectItem key={p.id} value={p.slug}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Prompt</Label>
          <Select
            value={prompt}
            onValueChange={(v) => setParams({ project, prompt: v })}
            disabled={!project}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select prompt" />
            </SelectTrigger>
            <SelectContent>
              {prompts.data?.map((p) => (
                <SelectItem key={p.id} value={p.name}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Target</Label>
          <Select value={target} onValueChange={setTarget} disabled={!prompt}>
            <SelectTrigger>
              <SelectValue placeholder="Version or tag" />
            </SelectTrigger>
            <SelectContent>
              {tags && tags.length > 0 && (
                <SelectGroup>
                  <SelectLabel>Tags</SelectLabel>
                  {tags.map((t) => (
                    <SelectItem key={t.name} value={`tag:${t.name}`}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              )}
              <SelectGroup>
                <SelectLabel>Versions</SelectLabel>
                {versions?.map((v) => (
                  <SelectItem key={v.id} value={`ver:${v.version}`}>
                    v{v.version}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>

      {!ready ? (
        <EmptyState
          icon={Wand2}
          title="Pick a prompt to render"
          description="Choose a project, prompt, and version or tag above."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Variables</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {variables.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  This version has no variables.
                </p>
              )}
              {variables.map((spec) => (
                <div key={spec.name} className="space-y-1.5">
                  <Label htmlFor={`var-${spec.name}`} className="font-mono">
                    {spec.name}
                    {spec.required && (
                      <span className="ml-1 text-destructive">*</span>
                    )}
                  </Label>
                  <Textarea
                    id={`var-${spec.name}`}
                    value={values[spec.name] ?? ""}
                    onChange={(e) => setField(spec.name, e.target.value)}
                    className="min-h-16 text-sm"
                    placeholder={spec.description ?? ""}
                  />
                </div>
              ))}
              <Button
                onClick={run}
                disabled={render.isPending}
                className="w-full gap-2"
              >
                <Sparkles className="size-4" />
                {render.isPending ? "Rendering..." : "Render"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Output</CardTitle>
            </CardHeader>
            <CardContent>
              <AnimatePresence mode="wait">
                {render.data ? (
                  <motion.div
                    key={`${render.data.version}-${render.submittedAt}`}
                    initial={{ opacity: 0, scale: 0.99, y: 6 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={easeOut}
                    className="space-y-3"
                  >
                    {render.data.system_prompt && (
                      <Output label="System" text={render.data.system_prompt} />
                    )}
                    <Output label="User" text={render.data.user_prompt} />
                  </motion.div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Fill the variables and render to see the result.
                  </p>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

function Output({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          {label}
        </span>
        <CopyButton value={text} />
      </div>
      <pre className="overflow-x-auto rounded-lg bg-muted/60 p-3 font-mono text-xs whitespace-pre-wrap">
        {text}
      </pre>
    </div>
  )
}
