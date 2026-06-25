import { motion } from "motion/react"
import { Boxes, FolderGit2, Trash2 } from "lucide-react"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { EmptyState } from "@/components/empty-state"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { CreateProjectDialog } from "@/features/projects/create-project-dialog"
import { useDeleteProject, useProjects } from "@/lib/api/hooks"
import { errorMessage, formatDate } from "@/lib/format"
import { listContainer, listItem } from "@/lib/motion"

export function ProjectsPage() {
  const { data: projects, isLoading, isError, error } = useProjects()
  const del = useDeleteProject()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Each project is a namespace for prompts and API keys."
        actions={<CreateProjectDialog />}
      />

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      )}

      {isError && (
        <EmptyState
          icon={Boxes}
          title="Could not load projects"
          description={errorMessage(error)}
        />
      )}

      {projects && projects.length === 0 && (
        <EmptyState
          icon={FolderGit2}
          title="No projects yet"
          description="Create your first project to start managing prompts."
          action={<CreateProjectDialog />}
        />
      )}

      {projects && projects.length > 0 && (
        <motion.div
          variants={listContainer}
          initial="hidden"
          animate="show"
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {projects.map((p) => (
            <motion.div key={p.id} variants={listItem}>
              <Card className="group h-full transition-shadow hover:shadow-md">
                <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
                  <Link to={`/projects/${p.slug}`} className="min-w-0">
                    <CardTitle className="truncate">{p.name}</CardTitle>
                    <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
                      {p.slug}
                    </p>
                  </Link>
                  <ConfirmDialog
                    title={`Delete “${p.name}”?`}
                    description="This permanently deletes the project and all its prompts, versions, and keys."
                    onConfirm={async () => {
                      try {
                        await del.mutateAsync(p.slug)
                        toast.success("Project deleted")
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
                </CardHeader>
                <CardContent>
                  <Link to={`/projects/${p.slug}`}>
                    <p className="line-clamp-2 min-h-10 text-sm text-muted-foreground">
                      {p.description || "No description"}
                    </p>
                    <p className="mt-3 text-xs text-muted-foreground">
                      Created {formatDate(p.created_at)}
                    </p>
                  </Link>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  )
}
