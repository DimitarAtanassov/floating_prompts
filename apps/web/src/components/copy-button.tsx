import { CheckIcon, CopyIcon } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/** Copies text to the clipboard with a brief confirmation. */
export function CopyButton({
  value,
  className,
  label = "Copy",
}: {
  value: string
  className?: string
  label?: string
}) {
  const [copied, setCopied] = useState(false)

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={cn("gap-1.5", className)}
      onClick={async () => {
        await navigator.clipboard.writeText(value)
        setCopied(true)
        setTimeout(() => setCopied(false), 1200)
      }}
    >
      {copied ? (
        <CheckIcon className="size-3.5 text-emerald-600" />
      ) : (
        <CopyIcon className="size-3.5" />
      )}
      {copied ? "Copied" : label}
    </Button>
  )
}
