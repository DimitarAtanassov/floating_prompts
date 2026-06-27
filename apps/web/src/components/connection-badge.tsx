import { Link } from "react-router-dom"
import { useHealth } from "@/lib/api/hooks"
import { cn } from "@/lib/utils"

/** Small live indicator of API reachability and whether a key is set. */
export function ConnectionBadge() {
  const { data, isLoading } = useHealth()

  const state = isLoading
    ? { dot: "bg-muted-foreground/50", label: "Checking..." }
    : !data?.ok
      ? { dot: "bg-destructive", label: "Unreachable" }
      : { dot: "bg-emerald-500", label: "Connected" }

  return (
    <Link
      to="/settings"
      className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent"
      title="Connection settings"
    >
      <span className={cn("size-2 rounded-full", state.dot)} />
      {state.label}
    </Link>
  )
}
