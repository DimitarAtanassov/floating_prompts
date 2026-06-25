import { Tag as TagIcon, Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useDeleteTag, useSetTag, useTags } from "@/lib/api/hooks"
import type { PromptVersion } from "@/lib/api/models"
import { errorMessage } from "@/lib/format"

export function TagsPanel({
  slug,
  name,
  versions,
}: {
  slug: string
  name: string
  versions: PromptVersion[]
}) {
  const { data: tags } = useTags(slug, name)
  const setTag = useSetTag(slug, name)
  const delTag = useDeleteTag(slug, name)
  const [tagName, setTagName] = useState("")
  const [version, setVersion] = useState<string>(
    versions[0] ? String(versions[0].version) : "",
  )

  const versionOf = (versionId: number) =>
    versions.find((v) => v.id === versionId)?.version ?? "?"

  async function apply() {
    if (!tagName.trim() || !version) return
    try {
      await setTag.mutateAsync({ tag: tagName.trim(), version: Number(version) })
      toast.success(`Tag “${tagName}” → v${version}`)
      setTagName("")
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {tags && tags.length > 0 ? (
          tags.map((t) => (
            <Badge
              key={t.name}
              variant="outline"
              className="gap-1.5 border-primary/30 bg-primary/5 py-1 pr-1 pl-2.5 text-sm"
            >
              <TagIcon className="size-3 text-primary" />
              <span className="font-medium">{t.name}</span>
              <span className="text-muted-foreground">
                v{versionOf(t.version_id)}
              </span>
              <button
                type="button"
                className="ml-1 rounded p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                onClick={async () => {
                  try {
                    await delTag.mutateAsync(t.name)
                    toast.success(`Removed tag “${t.name}”`)
                  } catch (err) {
                    toast.error(errorMessage(err))
                  }
                }}
              >
                <Trash2 className="size-3" />
              </button>
            </Badge>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No tags yet.</p>
        )}
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <Input
          value={tagName}
          onChange={(e) => setTagName(e.target.value)}
          placeholder="production"
          className="w-40"
        />
        <Select value={version} onValueChange={setVersion}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="version" />
          </SelectTrigger>
          <SelectContent>
            {versions.map((v) => (
              <SelectItem key={v.id} value={String(v.version)}>
                v{v.version}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="secondary"
          onClick={apply}
          disabled={setTag.isPending || !tagName.trim()}
        >
          Set tag
        </Button>
      </div>
    </div>
  )
}
