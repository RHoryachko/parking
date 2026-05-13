import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { LogsPage } from "./pages/LogsPage";
import { ParkingDetailsPage } from "./pages/ParkingDetailsPage";
import { ParkingsListPage } from "./pages/ParkingsListPage";
import { ParkingsMapPage } from "./pages/ParkingsMapPage";
import { WorkerDashboardPage } from "./pages/WorkerDashboardPage";
import { WorkerSessionsPage } from "./pages/WorkerSessionsPage";
import { WorkersPage } from "./pages/WorkersPage";

function RequireRole({ role }: { role: "admin" | "worker" }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="p-10 text-center text-sm text-zinc-600">Loading…</div>;
  }
  if (!user || user.role !== role) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-sm text-zinc-600">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "admin") return <Navigate to="/admin/dashboard" replace />;
  if (user.role === "worker") return <Navigate to="/worker/dashboard" replace />;
  return <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route element={<RequireRole role="admin" />}>
        <Route element={<Layout />}>
          <Route path="admin/dashboard" element={<DashboardPage />} />
          <Route path="admin/parkings" element={<ParkingsListPage />} />
          <Route path="admin/parkings/map" element={<ParkingsMapPage />} />
          <Route path="admin/parkings/:id" element={<ParkingDetailsPage />} />
          <Route path="admin/workers" element={<WorkersPage />} />
          <Route path="admin/logs" element={<LogsPage />} />
        </Route>
      </Route>

      <Route element={<RequireRole role="worker" />}>
        <Route element={<Layout />}>
          <Route path="worker/dashboard" element={<WorkerDashboardPage />} />
          <Route path="worker/sessions" element={<WorkerSessionsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}
