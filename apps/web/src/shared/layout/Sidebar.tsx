import { NavLink } from "react-router-dom";

import { useLogoutAction } from "../../features/auth/useLogoutAction";
import { useAuthStore } from "../../features/auth/store";
import { usePluginFrontendRuntime } from "../../features/plugins/runtime";
import { buildShellSidebarSections } from "../../features/shell/navigation";

export function Sidebar() {
  const logout = useLogoutAction();
  const permissions = useAuthStore((state) => state.permissions);
  const pluginRuntime = usePluginFrontendRuntime();
  const sections = buildShellSidebarSections({
    permissions,
    pluginNavigation: pluginRuntime.navigation,
  });

  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800 bg-slate-950/80 p-4">
      <div className="mb-8 space-y-1">
        <h1 className="text-lg font-semibold text-white">SYSTUTOR OSS</h1>
        <p className="text-sm text-slate-400">Core Frontend v0.2</p>
      </div>

      <nav className="space-y-5">
        {sections.map((section) => (
          <div key={section.title} className="space-y-2">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {section.title}
            </h2>

            <div className="space-y-2">
              {section.items.map((item) =>
                item.kind === "link" ? (
                  <NavLink
                    key={`${section.title}:${item.to}`}
                    to={item.to}
                    className={({ isActive }) =>
                      [
                        "block rounded-md px-3 py-2 text-sm transition",
                        isActive
                          ? "bg-slate-800 text-white"
                          : "text-slate-300 hover:bg-slate-900 hover:text-white",
                      ].join(" ")
                    }
                  >
                    {item.label}
                  </NavLink>
                ) : (
                  <button
                    key={`${section.title}:${item.action}`}
                    type="button"
                    onClick={logout}
                    className="block w-full rounded-md px-3 py-2 text-left text-sm text-slate-300 transition hover:bg-slate-900 hover:text-white"
                  >
                    {item.label}
                  </button>
                )
              )}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-auto rounded-md border border-dashed border-slate-800 p-3 text-xs text-slate-500">
        {pluginRuntime.navigation.length > 0
          ? "Shell tenant-aware con navegacion dinamica de plugins habilitados."
          : "No hay plugins habilitados visibles para este usuario."}
      </div>
    </aside>
  );
}
