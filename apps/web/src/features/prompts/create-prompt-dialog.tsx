import { zodResolver } from "@hookform/resolvers/zod"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { z } from "zod"
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
import { useCreatePrompt } from "@/lib/api/hooks"
import { errorMessage } from "@/lib/format"

const schema = z.object({
  name: z
    .string()
    .regex(
      /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$/,
      "Letters, digits, dot, dash, underscore",
    ),
  description: z.string().optional(),
})
type Values = z.infer<typeof schema>

export function CreatePromptDialog({ slug }: { slug: string }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const create = useCreatePrompt(slug)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) })

  async function onSubmit(values: Values) {
    try {
      const prompt = await create.mutateAsync({
        name: values.name,
        description: values.description || null,
      })
      toast.success(`Prompt “${prompt.name}” created`)
      setOpen(false)
      reset()
      navigate(`/projects/${slug}/prompts/${prompt.name}`)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="size-4" />
          New prompt
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create prompt</DialogTitle>
            <DialogDescription>
              A prompt holds versions. You add content in the next step.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="summarizer" {...register("name")} />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Input id="description" {...register("description")} />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
