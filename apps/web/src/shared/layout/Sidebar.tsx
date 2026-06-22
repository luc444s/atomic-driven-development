import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/app/system", label: "Sistema" },
  { to: "/app/plugins", label: "Plugins" },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800 bg-slate-950/80 p-4">
      <div className="mb-8 space-y-1">
        <h1 className="text-lg font-semibold text-white">SYSTUTOR OSS</h1>
        <p className="text-sm text-slate-400">Frontend Shell v0.1</p>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
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
        ))}
      </nav>

      <div className="mt-auto rounded-md border border-dashed border-slate-800 p-3 text-xs text-slate-500">
        La navegacion de plugins queda preparada para futuras extensiones del runtime frontend.
      </div>
    </aside>
  );
}
