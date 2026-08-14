import { lazy, Suspense } from "react";

import type { ComponentProps } from "react";

import type { RouteContextMap } from "./RouteContextMap";

const LazyRouteContextMap = lazy(() =>
  import("./RouteContextMap").then((module) => ({ default: module.RouteContextMap }))
);

export function RouteContextMapLazy(props: ComponentProps<typeof RouteContextMap>) {
  return (
    <Suspense fallback={null}>
      <LazyRouteContextMap {...props} />
    </Suspense>
  );
}
