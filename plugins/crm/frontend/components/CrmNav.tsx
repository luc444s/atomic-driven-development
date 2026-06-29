import { NavLink } from "../../../../apps/web/src/lib/router";

const NAV_ITEMS = [
  { to: "/app/crm/customers", label: "Clientes" },
  { to: "/app/crm/customers/new", label: "Nuevo" },
];

export function CrmNav() {
  return (
    <nav className="flex flex-wrap gap-2">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            [
              "rounded-md border px-3 py-1.5 text-sm transition",
              isActive
                ? "border-cyan-500 bg-cyan-500/10 text-cyan-300"
                : "border-slate-800 bg-slate-950 text-slate-300 hover:border-slate-700 hover:text-white",
            ].join(" ")
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
