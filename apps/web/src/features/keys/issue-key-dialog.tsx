import { KeyRound, Plus, TriangleAlert } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { CopyButton } from "@/components/copy-button"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useIssueApiKey } from "@/lib/api/hooks"
import { SCOPES, type Scope } from "@/lib/api/models"
import { cn } from "@/lib/utils"
import { errorMessage } from "@/lib/format"

export function IssueKeyDialog({ projectSlug }: { projectSlug: string }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [scopes, setScopes] = useState<Scope[]>(["read"])
  const [secret, setSecret] = useState<string | null>(null)
  const issue = useIssueApiKey(projectSlug)

  function toggle(scope: Scope) {
    setScopes((curr) =>
      curr.includes(scope)
        ? curr.filter((s) => s !== scope)
        : [...curr, scope],
    )
  }

  function reset() {
    setName("")
    setScopes(["read"])
    setSecret(null)
  }

  async function create() {
    if (!name.trim()) {
      toast.error("Name is required")
      return
    }
    try {
      const created = await issue.mutateAsync({
        name: name.trim(),
        scopes,
        project_slug: projectSlug,
      })
      setSecret(created.key)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="size-4" />
          Issue key
        </Button>
      </DialogTrigger>
      <DialogContent>
        {secret ? (
          <>
            <DialogHeader>
              <DialogTitle>API key created</DialogTitle>
              <DialogDescription className="flex items-center gap-1.5 text-amber-600">
                <TriangleAlert className="size-4" />
                Copy it now. It will not be shown again.
              </DialogDescription>
            </DialogHeader>
            <div className="my-2 flex items-center gap-2 rounded-lg border bg-muted/60 p-3">
              <code className="min-w-0 flex-1 truncate font-mono text-sm">
                {secret}
              </code>
              <CopyButton value={secret} />
            </div>
            <DialogFooter>
              <Button onClick={() => setOpen(false)}>Done</Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Issue API key</DialogTitle>
              <DialogDescription>
                Scoped to project{" "}
                <span className="font-mono">{projectSlug}</span>.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="key-name">Name</Label>
                <Input
                  id="key-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="ci-pipeline"
                />
              </div>
              <div className="space-y-2">
                <Label>Scopes</Label>
                <div className="flex gap-2">
                  {SCOPES.map((scope) => (
                    <button
                      key={scope}
                      type="button"
                      onClick={() => toggle(scope)}
                      className={cn(
                        "rounded-full border px-3 py-1 text-sm capitalize transition-colors",
                        scopes.includes(scope)
                          ? "border-primary bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:bg-accent",
                      )}
                    >
                      {scope}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={create}
                disabled={issue.isPending || scopes.length === 0}
                className="gap-2"
              >
                <KeyRound className="size-4" />
                {issue.isPending ? "Creating..." : "Create key"}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
