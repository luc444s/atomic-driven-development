import type {
  LogisticsDeliveryPoint,
  LogisticsRouteStop,
  RouteControlState,
  VehicleLocationEvent,
} from "../../api";
import { DEFAULT_MAP_CENTER } from "../route-builder/map-defaults";
import { decodePolyline } from "./route-polyline";

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
  assignedPath: LatLng[];
  traveledPath: LatLng[];
  stops: RouteControlMapStop[];
  startPoint: { position: LatLng; label: string } | null;
  vehiclePosition: LatLng | null;
};

const DEFAULT_CENTER = DEFAULT_MAP_CENTER;

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

function getStopCoordinates(stop: LogisticsRouteStop): LatLng | null {
  const raw = stop.gps_coordinates;
  if (!raw) {
    return null;
  }
  const coords = typeof raw === "string" ? JSON.parse(raw) : raw;
  if (typeof coords.lat !== "number" || typeof coords.lng !== "number") {
    return null;
  }
  return { lat: coords.lat, lng: coords.lng };
}

export function buildRouteControlMapView(args: {
  stops: LogisticsRouteStop[];
  deliveryPoints: LogisticsDeliveryPoint[];
  controlState: RouteControlState | null;
  history: VehicleLocationEvent[];
  assignedPolyline?: string | null;
  startPoint?: { lat: number; lng: number; label?: string | null } | null;
}): RouteControlMapView {
  const pointsById = new Map(args.deliveryPoints.map((point) => [point.id, point]));
  const stops = args.stops
    .map((stop) => {
      const deliveryPoint = pointsById.get(stop.delivery_point_id ?? "");
      const position = deliveryPoint
        ? getDeliveryPointCoordinates(deliveryPoint)
        : getStopCoordinates(stop);
      if (!position) {
        return null;
      }
      return {
        id: stop.id,
        label: `Parada ${stop.stop_order} · ${deliveryPoint?.customer_name ?? deliveryPoint?.address ?? stop.customer_name_snapshot ?? stop.id}`,
        position,
        isActive: args.controlState?.active_stop_id === stop.id,
        isCurrent: args.controlState?.current_stop_id === stop.id,
      };
    })
    .filter((item): item is RouteControlMapStop => item !== null);

  let assignedPath: LatLng[] = [];
  if (args.assignedPolyline) {
    try {
      assignedPath = decodePolyline(args.assignedPolyline);
    } catch {
      assignedPath = [];
    }
  }

  const startMarker = args.startPoint
    ? { position: { lat: args.startPoint.lat, lng: args.startPoint.lng }, label: args.startPoint.label ?? "Inicio" }
    : null;

  const traveledPath = args.history.map((event) => ({ lat: event.lat, lng: event.lng }));
  const plannedPath = [
    ...(startMarker ? [startMarker.position] : []),
    ...stops.map((stop) => stop.position),
  ];
  const lastHistoryPoint = traveledPath.length ? traveledPath[traveledPath.length - 1] : null;
  const vehiclePosition = args.controlState?.last_lat != null && args.controlState?.last_lng != null
    ? { lat: args.controlState.last_lat, lng: args.controlState.last_lng }
    : lastHistoryPoint;
  const center = vehiclePosition ?? assignedPath[0] ?? plannedPath[0] ?? DEFAULT_CENTER;
  const zoom = 12;

  return {
    center,
    zoom,
    plannedPath,
    assignedPath,
    traveledPath,
    stops,
    startPoint: startMarker,
    vehiclePosition,
  };
}
