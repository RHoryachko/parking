import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Input } from "../components/Input";

export function LoginPage() {
  const { user, loading, login, logout } = useAuth();
  const [email, setEmail] = useState("admin@parking.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && (user?.role === "admin" || user?.role === "worker")) {
    return <Navigate to={user.role === "admin" ? "/admin/dashboard" : "/"} replace />;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(email, password);
      if (me.role !== "admin" && me.role !== "worker") {
        logout();
        setError("Web app is available for admin/worker only.");
        return;
      }
    } catch {
      setError("Invalid credentials.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Parking</div>
          <div className="text-3xl font-semibold tracking-tight text-zinc-900">Sign in</div>
          <div className="mt-2 text-sm text-zinc-600">Use seeded admin or worker account from README.</div>
        </div>
        <Card>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="mb-2 block text-xs font-semibold text-zinc-600">Email</label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold text-zinc-600">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            {error ? <div className="text-sm text-red-600">{error}</div> : null}
            <Button className="w-full" type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Continue"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
