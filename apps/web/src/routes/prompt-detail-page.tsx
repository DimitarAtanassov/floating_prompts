import { motion } from "motion/react"
import { ChevronLeft, Wand2 } from "lucide-react"
import { Link, useParams } from "react-router-dom"
import { EmptyState } from "@/components/empty-state"
import { PageHeader } from "@/components/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NewVersionDialog } from "@/features/versions/new-version-dialog"
import { TagsPanel } from "@/features/tags/tags-panel"
import { useVersions } from "@/lib/api/hooks"
import { formatDate } from "@/lib/format"
import { listContainer, listItem } from "@/lib/motion"
import { GitCommitVertical } from "lucide-react"

export function PromptDetailPage() {
  const { slug = "", name = "" } = useParams()
  const { data: versions, isLoading } = useVersions(slug, name)

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/projects/${slug}`}
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-4" />
          {slug}
        </Link>
        <PageHeader
          title={name}
          description="Immutable versions and movable environment tags."
          actions={
            <div className="flex gap-2">
              <Button variant="outline" asChild className="gap-2">
                <Link to={`/playground?project=${slug}&prompt=${name}`}>
                  <Wand2 className="size-4" />
                  Playground
                </Link>
              </Button>
              <NewVersionDialog slug={slug} name={name} />
            </div>
          }
        />
      </div>

      {isLoading && <Skeleton className="h-48 rounded-xl" />}

      {versions && (
        <Tabs defaultValue="versions">
          <TabsList>
            <TabsTrigger value="versions">
              Versions {versions.length > 0 && `(${versions.length})`}
            </TabsTrigger>
            <TabsTrigger value="tags">Tags</TabsTrigger>
          </TabsList>

          <TabsContent value="versions" className="mt-4">
            {versions.length === 0 ? (
              <EmptyState
                icon={GitCommitVertical}
                title="No versions yet"
                description="Create the first version with a template."
                action={<NewVersionDialog slug={slug} name={name} />}
              />
            ) : (
              <motion.div
                variants={listContainer}
                initial="hidden"
                animate="show"
                className="space-y-4"
              >
                {versions.map((v) => (
                  <motion.div key={v.id} variants={listItem}>
                    <Card>
                      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
                        <div className="flex items-center gap-3">
                          <Badge className="font-mono">v{v.version}</Badge>
                          <span className="text-sm text-muted-foreground">
                            {formatDate(v.created_at)}
                            {v.created_by && ` · ${v.created_by}`}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {v.variables.map((spec) => (
                            <Badge
                              key={spec.name}
                              variant="secondary"
                              className="font-mono text-xs"
                            >
                              {spec.name}
                            </Badge>
                          ))}
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {v.system_prompt && (
                          <div>
                            <div className="mb-1 text-xs font-medium text-muted-foreground">
                              System
                            </div>
                            <pre className="overflow-x-auto rounded-lg bg-muted/60 p-3 font-mono text-xs whitespace-pre-wrap">
                              {v.system_prompt}
                            </pre>
                          </div>
                        )}
                        <div>
                          <div className="mb-1 text-xs font-medium text-muted-foreground">
                            User
                          </div>
                          <pre className="overflow-x-auto rounded-lg bg-muted/60 p-3 font-mono text-xs whitespace-pre-wrap">
                            {v.user_prompt}
                          </pre>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </TabsContent>

          <TabsContent value="tags" className="mt-4">
            <Card>
              <CardContent className="py-6">
                <TagsPanel slug={slug} name={name} versions={versions} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
