import { AnimatePresence, motion } from "motion/react"
import { FolderGit2, Settings, Sparkles, Wand2 } from "lucide-react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import { ConnectionBadge } from "@/components/connection-badge"
import { pageMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

const NAV = [
  { to: "/projects", label: "Projects", icon: FolderGit2 },
  { to: "/playground", label: "Playground", icon: Wand2 },
  { to: "/settings", label: "Settings", icon: Settings },
]

export function AppShell() {
  const location = useLocation()

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-sidebar px-4 py-5 md:flex">
        <div className="flex items-center gap-2 px-2 pb-6">
          <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Sparkles className="size-5" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold text-foreground">
              Floating Prompts
            </div>
            <div className="text-xs text-muted-foreground">Prompt manager</div>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-1 pt-4 text-xs text-muted-foreground">
          v0.1 &middot; light
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-3 border-b bg-background/80 px-6 backdrop-blur">
          <nav className="flex items-center gap-1 md:hidden">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-md p-2 text-muted-foreground",
                    isActive && "bg-accent text-accent-foreground",
                  )
                }
                title={item.label}
              >
                <item.icon className="size-4" />
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto">
            <ConnectionBadge />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              className="mx-auto max-w-6xl px-6 py-8"
              {...pageMotion}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
