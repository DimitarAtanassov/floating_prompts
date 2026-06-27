import { GitCommitVertical } from "lucide-react"
import { useMemo, useState } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useCreateVersion } from "@/lib/api/hooks"
import { errorMessage } from "@/lib/format"
import { detectVariables } from "@/lib/template"

export function NewVersionDialog({
  slug,
  name,
  initialSystem = "",
  initialUser = "",
}: {
  slug: string
  name: string
  initialSystem?: string
  initialUser?: string
}) {
  const [open, setOpen] = useState(false)
  const [system, setSystem] = useState(initialSystem)
  const [user, setUser] = useState(initialUser)
  const create = useCreateVersion(slug, name)

  const variables = useMemo(
    () => detectVariables(system, user),
    [system, user],
  )

  async function submit() {
    if (!user.trim()) {
      toast.error("User prompt is required")
      return
    }
    try {
      const version = await create.mutateAsync({
        user_prompt: user,
        system_prompt: system.trim() ? system : null,
        variables: null, // inferred by the server from the templates
      })
      toast.success(`Version ${version.version} created`)
      setOpen(false)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <GitCommitVertical className="size-4" />
          New version
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New version of “{name}”</DialogTitle>
          <DialogDescription>
            Use <code className="text-xs">{"{{ variable }}"}</code> placeholders.
            Versions are immutable and auto-numbered.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="system">System prompt (optional)</Label>
            <Textarea
              id="system"
              value={system}
              onChange={(e) => setSystem(e.target.value)}
              placeholder="You are a concise assistant."
              className="min-h-20 font-mono text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="user">User prompt</Label>
            <Textarea
              id="user"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              placeholder={"Summarize the following:\n\n{{ content }}"}
              className="min-h-32 font-mono text-sm"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Detected variables:
            </span>
            {variables.length === 0 ? (
              <span className="text-sm text-muted-foreground">none</span>
            ) : (
              variables.map((v) => (
                <Badge key={v} variant="secondary" className="font-mono">
                  {v}
                </Badge>
              ))
            )}
          </div>
        </div>

        <DialogFooter>
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? "Saving..." : "Save version"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
