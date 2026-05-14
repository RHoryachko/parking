import { Navigate } from "react-router-dom";

/** @deprecated Use `/worker/lot` — kept for old bookmarks. */
export function WorkerSessionsPage() {
  return <Navigate to="/worker/lot" replace />;
}
