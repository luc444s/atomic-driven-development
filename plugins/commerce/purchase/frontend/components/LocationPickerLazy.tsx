import { lazy, Suspense } from "react";

import type { ComponentProps } from "react";

import type { LocationPicker } from "@systutor/shell/ui/location-picker";

// Import diferido: evita arrastrar leaflet a entornos sin window (tests node,
// registros de plugins que solo inspeccionan rutas).
const LazyLocationPicker = lazy(() =>
  import("@systutor/shell/ui/location-picker").then((module) => ({
    default: module.LocationPicker,
  }))
);

export function LocationPickerLazy(props: ComponentProps<typeof LocationPicker>) {
  return (
    <Suspense fallback={<div className="h-[220px] rounded-md border border-border bg-muted/30" />}>
      <LazyLocationPicker {...props} />
    </Suspense>
  );
}
