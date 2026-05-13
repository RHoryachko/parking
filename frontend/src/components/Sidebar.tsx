import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition ${
    isActive ? "bg-white/80 text-zinc-900 shadow-sm ring-1 ring-black/5" : "text-zinc-600 hover:bg-black/5"
  }`;

export function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const base = isAdmin ? "/admin" : "/worker";

  return (
    <aside className="hidden w-64 shrink-0 flex-col gap-2 border-r border-black/5 bg-white/50 p-4 backdrop-blur-xl md:flex">
      <div className="mb-6 px-2">
        <div className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Parking</div>
        <div className="text-lg font-semibold text-zinc-900">
          {isAdmin ? "Admin" : "Worker"}
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        <NavLink to={`${base}/dashboard`} end className={linkClass}>
          Dashboard
        </NavLink>
        {isAdmin ? (
          <>
            <NavLink to="/admin/parkings" className={linkClass}>
              Parkings
            </NavLink>
            <NavLink to="/admin/parkings/map" className={linkClass}>
              Map
            </NavLink>
            <NavLink to="/admin/workers" className={linkClass}>
              Workers
            </NavLink>
            <NavLink to="/admin/logs" className={linkClass}>
              Logs
            </NavLink>
          </>
        ) : (
          <NavLink to="/worker/sessions" className={linkClass}>
            Sessions
          </NavLink>
        )}
      </nav>
      <div className="mt-auto rounded-2xl border border-black/5 bg-gradient-to-br from-indigo-500/10 to-sky-500/10 p-4 text-xs text-zinc-700">
        Tip: keep the API running on <span className="font-mono">:8000</span> and use the Vite proxy for{" "}
        <span className="font-mono">/api</span>.
      </div>
    </aside>
  );
}
