import { Button } from "@systutor/shell/ui/button";
import type { LogisticsRoute } from "../../api";
import { formatRouteLabel } from "../../lib/route-labels";

type Props = {
  routes: LogisticsRoute[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  onEditRoute: (routeId: string) => void;
  onNewRoute: () => void;
};

export function RouteListSidebar({
  routes,
  selectedRouteId,
  onSelectRoute,
  onEditRoute,
  onNewRoute,
}: Props) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-foreground">Rutas guardadas</p>
        <Button variant="secondary" onClick={onNewRoute}>+ Nueva</Button>
      </div>

      {routes.length ? (
        <div className="space-y-2">
          {routes.map((route) => {
            const displayName = formatRouteLabel(route);
            const isSelected = route.id === selectedRouteId;

            return (
              <div
                key={route.id}
                className={`rounded-lg border px-3 py-2 text-sm ${
                  isSelected ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                <p className="font-medium text-foreground">{displayName}</p>
                <p className="text-xs text-muted-foreground">
                  {route.route_date} · {route.status}
                </p>
                <div className="mt-2 flex gap-2">
                  <Button variant="secondary" onClick={() => onSelectRoute(route.id)}>Ver</Button>
                  <Button variant="secondary" onClick={() => onEditRoute(route.id)}>Editar</Button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border p-4 text-center">
          <p className="text-sm text-muted-foreground">No hay rutas todavía.</p>
        </div>
      )}
    </div>
  );
}
