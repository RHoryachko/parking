import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

function titleForPath(pathname: string) {
  if (pathname.endsWith("/dashboard")) return "Dashboard";
  if (pathname.endsWith("/parkings/map")) return "Parkings map";
  if (/\/parkings\/\d+/.test(pathname)) return "Parking details";
  if (pathname.endsWith("/parkings")) return "Parkings";
  if (pathname.endsWith("/workers")) return "Workers";
  if (pathname.endsWith("/logs")) return "Logs";
  if (pathname.endsWith("/sessions")) return "Sessions";
  return "Parking Admin";
}

export function Layout() {
  const location = useLocation();
  const title = titleForPath(location.pathname);
  return (
    <div className="flex min-h-full">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} />
        <main className="flex-1 space-y-6 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
