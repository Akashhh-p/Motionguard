import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Bot, Camera, FileArchive, FileText, LayoutDashboard, Menu, Settings, ShieldCheck, SquareDashedMousePointer } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import clsx from "clsx";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live-monitoring", label: "Live", icon: Camera },
  { to: "/zones", label: "Zones", icon: SquareDashedMousePointer },
  { to: "/evidence", label: "Evidence", icon: FileArchive },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/assistant", label: "Assistant", icon: Bot },
  { to: "/settings", label: "Settings", icon: Settings }
];

export function AppLayout() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();
  const links = (
    <nav className="space-y-1">
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            clsx("flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition duration-200", isActive ? "bg-[#E7EBE2] text-[#5E6B4F] shadow-sm ring-1 ring-[#E5E7E1]" : "text-muted hover:bg-[#EDF0E8] hover:text-ink")
          }
        >
          <item.icon size={18} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen bg-canvas">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-[#E5E7E1] bg-[#F7F8F4]/92 px-5 py-6 shadow-premium backdrop-blur-xl lg:block">
        <div className="mb-8 flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-2xl bg-[#5E6B4F] text-white shadow-glow"><ShieldCheck size={20} /></div>
          <div>
            <p className="text-sm font800 font-bold text-ink">MotionGuard AI</p>
            <p className="text-xs text-muted">Enterprise Intelligence</p>
          </div>
        </div>
        {links}
      </aside>
      {open && <div className="fixed inset-0 z-40 bg-[#1F2937]/30 lg:hidden" onClick={() => setOpen(false)} />}
      <aside className={clsx("fixed inset-y-0 left-0 z-50 w-72 border-r border-[#E5E7E1] bg-[#F7F8F4] px-5 py-6 transition lg:hidden", open ? "translate-x-0" : "-translate-x-full")}>{links}</aside>
      <main className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[#E5E7E1] bg-[#F7F8F4]/84 px-4 backdrop-blur-xl sm:px-6">
          <button className="grid size-10 place-items-center rounded-2xl border border-[#E5E7E1] bg-[#EFF2EC] lg:hidden" onClick={() => setOpen(true)}><Menu size={20} /></button>
          <div className="hidden lg:block">
            <p className="text-sm font-semibold text-ink">Security operations console</p>
            <p className="text-xs text-muted">Real-time detection, analytics, evidence, and reports</p>
          </div>
          <div className="flex items-center gap-3">
            <BarChart3 size={18} className="text-[#15803D]" />
            <div className="text-right">
              <p className="text-sm font-semibold text-ink">{user?.full_name}</p>
              <p className="text-xs text-muted">{user?.email}</p>
            </div>
          </div>
        </header>
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
