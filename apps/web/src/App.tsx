import { Navigate, Route, Routes } from "react-router-dom"
import { AppShell } from "./components/app-shell"
import { PlaygroundPage } from "./routes/playground-page"
import { ProjectDetailPage } from "./routes/project-detail-page"
import { ProjectsPage } from "./routes/projects-page"
import { PromptDetailPage } from "./routes/prompt-detail-page"
import { SettingsPage } from "./routes/settings-page"

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:slug" element={<ProjectDetailPage />} />
        <Route
          path="/projects/:slug/prompts/:name"
          element={<PromptDetailPage />}
        />
        <Route path="/playground" element={<PlaygroundPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/projects" replace />} />
      </Route>
    </Routes>
  )
}
