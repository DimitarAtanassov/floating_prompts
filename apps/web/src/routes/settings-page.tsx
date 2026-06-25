import { useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, Save, XCircle } from "lucide-react"
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
import { getBaseUrl, setSettings } from "@/lib/settings"

export function SettingsPage() {
  const qc = useQueryClient()
  const { data: health } = useHealth()
  const [baseUrl, setBaseUrl] = useState(getBaseUrl())

  function save() {
    setSettings({ baseUrl })
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
            The API base URL is stored in your browser only.
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
              <Save className="size-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
