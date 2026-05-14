import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { LogsPage } from "./pages/LogsPage";
import { ParkingDetailsPage } from "./pages/ParkingDetailsPage";
import { ParkingsListPage } from "./pages/ParkingsListPage";
import { ParkingsMapPage } from "./pages/ParkingsMapPage";
import { WorkerLotPage } from "./pages/WorkerLotPage";
import { WorkerSessionsPage } from "./pages/WorkerSessionsPage";
import { WorkersPage } from "./pages/WorkersPage";

/** Shared shell: auth gate + sidebar layout. Children use absolute paths `/admin/...`. */
function AdminLayoutShell() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="p-10 text-center text-sm text-zinc-600">Loading…</div>;
  }
  if (!user || user.role !== "admin") {
    return <Navigate to="/login" replace />;
  }
  return <Layout />;
}

function WorkerLayoutShell() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="p-10 text-center text-sm text-zinc-600">Loading…</div>;
  }
  if (!user || user.role !== "worker") {
    return <Navigate to="/login" replace />;
  }
  return <Layout />;
}

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-sm text-zinc-600">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "admin") return <Navigate to="/admin/dashboard" replace />;
  if (user.role === "worker") return <Navigate to="/worker/lot" replace />;
  return <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route element={<AdminLayoutShell />}>
        <Route path="/admin/dashboard" element={<DashboardPage />} />
        <Route path="/admin/parkings" element={<ParkingsListPage />} />
        <Route path="/admin/parkings/map" element={<ParkingsMapPage />} />
        <Route path="/admin/parkings/:id" element={<ParkingDetailsPage />} />
        <Route path="/admin/workers" element={<WorkersPage />} />
        <Route path="/admin/logs" element={<LogsPage />} />
      </Route>

      <Route element={<WorkerLayoutShell />}>
        <Route path="/worker/dashboard" element={<Navigate to="/worker/lot" replace />} />
        <Route path="/worker/lot" element={<WorkerLotPage />} />
        <Route path="/worker/sessions" element={<WorkerSessionsPage />} />
      </Route>

      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}
