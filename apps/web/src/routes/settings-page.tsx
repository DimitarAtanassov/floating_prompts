import { useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, KeyRound, XCircle } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useHealth } from "@/lib/api/hooks"
import { getApiKey, getBaseUrl, setSettings } from "@/lib/settings"

export function SettingsPage() {
  const qc = useQueryClient()
  const { data: health } = useHealth()
  const [baseUrl, setBaseUrl] = useState(getBaseUrl())
  const [apiKey, setApiKey] = useState(getApiKey())

  function save() {
    setSettings({ baseUrl, apiKey })
    qc.invalidateQueries()
    toast.success("Settings saved")
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Connect this UI to your Floating Prompts API."
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Connection</CardTitle>
          <CardDescription>
            Stored in your browser only. The API key is sent as the{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              X-API-Key
            </code>{" "}
            header.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="baseUrl">API base URL</Label>
            <Input
              id="baseUrl"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="apiKey">API key</Label>
            <Input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="fp_..."
            />
            <p className="text-xs text-muted-foreground">
              Create one with{" "}
              <code className="rounded bg-muted px-1 py-0.5">
                uv run floating-prompts bootstrap
              </code>{" "}
              or on the API Keys page.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              {health?.ok ? (
                <>
                  <CheckCircle2 className="size-4 text-emerald-600" />
                  <span className="text-muted-foreground">
                    Reachable (database {health.database ?? "?"})
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="size-4 text-destructive" />
                  <span className="text-muted-foreground">Not reachable</span>
                </>
              )}
            </div>
            <Button onClick={save} className="gap-2">
              <KeyRound className="size-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
