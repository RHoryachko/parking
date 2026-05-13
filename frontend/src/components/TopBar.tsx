import { useAuth } from "../auth/AuthContext";
import { Button } from "./Button";

export function TopBar({ title }: { title: string }) {
  const { user, logout } = useAuth();
  return (
    <header className="flex items-center justify-between gap-4 border-b border-black/5 bg-white/40 px-6 py-4 backdrop-blur-xl">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Overview</div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-900">{title}</h1>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <div className="text-sm font-medium text-zinc-900">{user?.full_name}</div>
          <div className="text-xs text-zinc-500">{user?.email}</div>
        </div>
        <Button variant="secondary" type="button" onClick={logout}>
          Log out
        </Button>
      </div>
    </header>
  );
}
