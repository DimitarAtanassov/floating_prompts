import { motion } from "motion/react"
import { ChevronLeft, FileText, KeyRound, Trash2 } from "lucide-react"
import { Link, useParams } from "react-router-dom"
import { toast } from "sonner"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { EmptyState } from "@/components/empty-state"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { CreatePromptDialog } from "@/features/prompts/create-prompt-dialog"
import { useDeletePrompt, useProject, usePrompts } from "@/lib/api/hooks"
import { errorMessage, formatDate } from "@/lib/format"
import { listContainer, listItem } from "@/lib/motion"

export function ProjectDetailPage() {
  const { slug = "" } = useParams()
  const project = useProject(slug)
  const { data: prompts, isLoading } = usePrompts(slug)
  const del = useDeletePrompt(slug)

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/projects"
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-4" />
          Projects
        </Link>
        <PageHeader
          title={project.data?.name ?? slug}
          description={project.data?.description ?? `Prompts in ${slug}`}
          actions={
            <div className="flex gap-2">
              <Button variant="outline" asChild className="gap-2">
                <Link to={`/keys?project=${slug}`}>
                  <KeyRound className="size-4" />
                  API keys
                </Link>
              </Button>
              <CreatePromptDialog slug={slug} />
            </div>
          }
        />
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      )}

      {prompts && prompts.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No prompts yet"
          description="Create a prompt, then add versions and tags."
          action={<CreatePromptDialog slug={slug} />}
        />
      )}

      {prompts && prompts.length > 0 && (
        <motion.div
          variants={listContainer}
          initial="hidden"
          animate="show"
          className="space-y-3"
        >
          {prompts.map((p) => (
            <motion.div key={p.id} variants={listItem}>
              <Card className="group transition-shadow hover:shadow-md">
                <CardContent className="flex items-center justify-between gap-4 py-4">
                  <Link
                    to={`/projects/${slug}/prompts/${p.name}`}
                    className="min-w-0 flex-1"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="size-4 shrink-0 text-primary" />
                      <span className="truncate font-medium">{p.name}</span>
                    </div>
                    <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">
                      {p.description || "No description"}
                    </p>
                  </Link>
                  <span className="hidden text-xs text-muted-foreground sm:block">
                    {formatDate(p.created_at)}
                  </span>
                  <ConfirmDialog
                    title={`Delete “${p.name}”?`}
                    description="This deletes the prompt and all its versions and tags."
                    onConfirm={async () => {
                      try {
                        await del.mutateAsync(p.name)
                        toast.success("Prompt deleted")
                      } catch (err) {
                        toast.error(errorMessage(err))
                      }
                    }}
                    trigger={
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-8 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    }
                  />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  )
}
