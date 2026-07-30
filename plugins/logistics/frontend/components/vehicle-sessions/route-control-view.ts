import type {
  LogisticsDeliveryPoint,
  LogisticsRouteStop,
  RouteControlState,
  VehicleLocationEvent,
} from "../../api";

type LatLng = { lat: number; lng: number };

export type RouteControlMapStop = {
  id: string;
  label: string;
  position: LatLng;
  isActive: boolean;
  isCurrent: boolean;
};

export type RouteControlMapView = {
  center: LatLng;
  zoom: number;
  plannedPath: LatLng[];
  traveledPath: LatLng[];
  stops: RouteControlMapStop[];
  vehiclePosition: LatLng | null;
};

const DEFAULT_CENTER: LatLng = { lat: -12.0464, lng: -77.0428 };

function getDeliveryPointCoordinates(point: LogisticsDeliveryPoint): LatLng | null {
  if (!point.gps_coordinates) {
    return null;
  }
  const { lat, lng } = point.gps_coordinates;
  if (typeof lat !== "number" || typeof lng !== "number") {
    return null;
  }
  return { lat, lng };
}

export function buildRouteControlMapView(args: {
  stops: LogisticsRouteStop[];
  deliveryPoints: LogisticsDeliveryPoint[];
  controlState: RouteControlState | null;
  history: VehicleLocationEvent[];
}): RouteControlMapView {
  const pointsById = new Map(args.deliveryPoints.map((point) => [point.id, point]));
  const stops = args.stops
    .map((stop) => {
      const deliveryPoint = pointsById.get(stop.delivery_point_id);
      const position = deliveryPoint ? getDeliveryPointCoordinates(deliveryPoint) : null;
      if (!position) {
        return null;
      }
      return {
        id: stop.id,
        label: `Parada ${stop.stop_order} · ${deliveryPoint?.customer_name ?? deliveryPoint?.address ?? stop.id}`,
        position,
        isActive: args.controlState?.active_stop_id === stop.id,
        isCurrent: args.controlState?.current_stop_id === stop.id,
      };
    })
    .filter((item): item is RouteControlMapStop => item !== null);

  const traveledPath = args.history.map((event) => ({ lat: event.lat, lng: event.lng }));
  const plannedPath = stops.map((stop) => stop.position);
  const lastHistoryPoint = traveledPath.length ? traveledPath[traveledPath.length - 1] : null;
  const vehiclePosition = args.controlState?.last_lat != null && args.controlState?.last_lng != null
    ? { lat: args.controlState.last_lat, lng: args.controlState.last_lng }
    : lastHistoryPoint;
  const center = vehiclePosition ?? plannedPath[0] ?? DEFAULT_CENTER;
  const zoom = vehiclePosition || plannedPath.length ? 12 : 6;

  return {
    center,
    zoom,
    plannedPath,
    traveledPath,
    stops,
    vehiclePosition,
  };
}
