import { motion } from "motion/react"
import { Ban, KeyRound } from "lucide-react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { EmptyState } from "@/components/empty-state"
import { PageHeader } from "@/components/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { IssueKeyDialog } from "@/features/keys/issue-key-dialog"
import { useApiKeys, useProjects, useRevokeApiKey } from "@/lib/api/hooks"
import { errorMessage, formatDate } from "@/lib/format"
import { listContainer, listItem } from "@/lib/motion"

export function ApiKeysPage() {
  const [params, setParams] = useSearchParams()
  const project = params.get("project") ?? ""
  const projects = useProjects()
  const { data: apiKeys, isLoading } = useApiKeys(project)
  const revoke = useRevokeApiKey(project)

  return (
    <div className="space-y-6">
      <PageHeader
        title="API Keys"
        description="Issue and revoke scoped keys. Secrets are shown once."
        actions={project ? <IssueKeyDialog projectSlug={project} /> : undefined}
      />

      <div className="max-w-xs space-y-1.5">
        <Label>Project</Label>
        <Select value={project} onValueChange={(v) => setParams({ project: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Select a project" />
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

      {!project && (
        <EmptyState
          icon={KeyRound}
          title="Choose a project"
          description="Select a project to view and manage its API keys."
        />
      )}

      {project && isLoading && <Skeleton className="h-32 rounded-xl" />}

      {project && apiKeys && apiKeys.length === 0 && (
        <EmptyState
          icon={KeyRound}
          title="No keys for this project"
          description="Issue a key to let apps and CI authenticate."
          action={<IssueKeyDialog projectSlug={project} />}
        />
      )}

      {project && apiKeys && apiKeys.length > 0 && (
        <motion.div
          variants={listContainer}
          initial="hidden"
          animate="show"
          className="space-y-3"
        >
          {apiKeys.map((k) => {
            const revoked = k.revoked_at != null
            return (
              <motion.div key={k.id} variants={listItem}>
                <Card className={revoked ? "opacity-60" : undefined}>
                  <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{k.name}</span>
                        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground">
                          {k.prefix}…
                        </code>
                        {revoked && <Badge variant="destructive">revoked</Badge>}
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                        {k.scopes.map((s) => (
                          <Badge
                            key={s}
                            variant="secondary"
                            className="text-xs capitalize"
                          >
                            {s}
                          </Badge>
                        ))}
                        <span className="ml-1 text-xs text-muted-foreground">
                          created {formatDate(k.created_at)}
                        </span>
                      </div>
                    </div>
                    {!revoked && (
                      <ConfirmDialog
                        title={`Revoke “${k.name}”?`}
                        description="Applications using this key will stop working immediately."
                        confirmLabel="Revoke"
                        onConfirm={async () => {
                          try {
                            await revoke.mutateAsync(k.id)
                            toast.success("Key revoked")
                          } catch (err) {
                            toast.error(errorMessage(err))
                          }
                        }}
                        trigger={
                          <Button variant="outline" size="sm" className="gap-1.5">
                            <Ban className="size-3.5" />
                            Revoke
                          </Button>
                        }
                      />
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </motion.div>
      )}
    </div>
  )
}
