import { NavLink } from "../../../../apps/web/src/lib/router";

const NAV_ITEMS = [
  { to: "/app/logistics", label: "Resumen" },
  { to: "/app/logistics/cylinders", label: "Envases" },
  { to: "/app/logistics/planning", label: "Planificacion" },
  { to: "/app/logistics/orders", label: "Pedidos" },
  { to: "/app/logistics/routes", label: "Rutas" },
  { to: "/app/logistics/loads", label: "Carga" },
  { to: "/app/logistics/movements", label: "Movimientos" },
  { to: "/app/logistics/reception", label: "Recepcion" },
  { to: "/app/logistics/agenda", label: "Agenda" },
  { to: "/app/logistics/equipment", label: "Equipos" },
  { to: "/app/logistics/warehouses", label: "Almacenes" },
  { to: "/app/logistics/vehicles", label: "Vehiculos" },
  { to: "/app/logistics/delivery-points", label: "Entregas" },
];

export function LogisticsNav() {
  return (
    <div className="overflow-x-auto">
      <nav className="flex min-w-max gap-2 rounded-xl border border-slate-800 bg-slate-950/60 p-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                "rounded-lg px-3 py-2 text-sm transition",
                isActive
                  ? "bg-slate-100 text-slate-950"
                  : "text-slate-400 hover:bg-slate-900 hover:text-white",
              ].join(" ")
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
