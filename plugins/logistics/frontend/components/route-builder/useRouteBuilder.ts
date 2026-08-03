import { useState } from "react";

import { useMutation, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { createRoute, createRouteStop, logisticsKeys } from "../../api";

export type BuilderPhase = "idle" | "picking_start" | "picking_end" | "picking_stops";

export type RouteStopDraft = {
  lat: number;
  lng: number;
  name: string;
  type: "start" | "end" | "stop";
};

type Props = {
  onError: (message: string) => void;
  onRouteCreated?: (routeId: string) => void;
};

export function useRouteBuilder({ onError, onRouteCreated }: Props) {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<BuilderPhase>("idle");
  const [startPoint, setStartPoint] = useState<RouteStopDraft | null>(null);
  const [endPoint, setEndPoint] = useState<RouteStopDraft | null>(null);
  const [stops, setStops] = useState<RouteStopDraft[]>([]);
  const [routeDate, setRouteDate] = useState(new Date().toISOString().slice(0, 10));
  const [vehicleId, setVehicleId] = useState("");
  const [customName, setCustomName] = useState("");
  const [editingRouteId, setEditingRouteId] = useState<string | null>(null);

  function buildDerivedName(startName: string | null, endName: string | null) {
    if (!startName || !endName) return "";
    return `${startName} → ${endName}`;
  }

  async function reverseGeocode(lat: number, lng: number): Promise<string> {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18`
      );
      const data = (await res.json()) as { display_name?: string };
      return data.display_name || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    } catch {
      return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    }
  }

  async function handleMapClick(lat: number, lng: number) {
    if (phase === "picking_start") {
      const name = await reverseGeocode(lat, lng);
      setStartPoint({ lat, lng, name, type: "start" });
      setPhase("picking_end");
      return;
    }

    if (phase === "picking_end") {
      const name = await reverseGeocode(lat, lng);
      setEndPoint({ lat, lng, name, type: "end" });
      setPhase("picking_stops");
      if (startPoint) {
        setCustomName(`${startPoint.name} → ${name}`);
      }
      return;
    }

    if (phase === "picking_stops") {
      const name = await reverseGeocode(lat, lng);
      setStops((current) => [
        ...current,
        { lat, lng, name, type: "stop" },
      ]);
    }
  }

  function removeStart() {
    setStartPoint(null);
    setPhase(endPoint ? "picking_end" : "picking_start");
  }

  function removeEnd() {
    setEndPoint(null);
    setStops([]);
    setPhase("picking_end");
  }

  function removeStop(index: number) {
    setStops((current) => current.filter((_, i) => i !== index));
  }

  function reorderStop(fromIndex: number, toIndex: number) {
    setStops((current) => {
      const next = [...current];
      const [item] = next.splice(fromIndex, 1);
      next.splice(toIndex, 0, item);
      return next;
    });
  }

  function startNew() {
    setPhase("picking_start");
    setStartPoint(null);
    setEndPoint(null);
    setStops([]);
    setCustomName("");
    setEditingRouteId(null);
  }

  function startEditing(routeId: string) {
    setEditingRouteId(routeId);
    setStartPoint(null);
    setEndPoint(null);
    setStops([]);
    setPhase("picking_start");
    setCustomName("");
  }

  function cancelBuilder() {
    setPhase("idle");
    setStartPoint(null);
    setEndPoint(null);
    setStops([]);
    setCustomName("");
    setEditingRouteId(null);
  }

  async function handleMarkerDrag(id: string, lat: number, lng: number) {
    if (id === "start" && startPoint) {
      const name = await reverseGeocode(lat, lng);
      setStartPoint({ ...startPoint, lat, lng, name });
      if (endPoint) {
        setCustomName(`${name} → ${endPoint.name}`);
      }
    } else if (id === "end" && endPoint) {
      const name = await reverseGeocode(lat, lng);
      setEndPoint({ ...endPoint, lat, lng, name });
      if (startPoint) {
        setCustomName(`${startPoint.name} → ${name}`);
      }
    } else if (id.startsWith("stop-")) {
      const index = parseInt(id.replace("stop-", ""));
      setStops((current) =>
        current.map((s, i) => (i === index ? { ...s, lat, lng } : s))
      );
    }
  }

  async function addStopManual() {
    if (phase !== "picking_stops") return;
    const lastStop = stops.length > 0 ? stops[stops.length - 1] : endPoint || startPoint;
    const lat = lastStop ? lastStop.lat + 0.002 : 0;
    const lng = lastStop ? lastStop.lng + 0.002 : 0;
    const name = await reverseGeocode(lat, lng);
    setStops((current) => [
      ...current,
      { lat, lng, name, type: "stop" as const },
    ]);
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const derived = customName || buildDerivedName(startPoint?.name ?? null, endPoint?.name ?? null);

      const route = await createRoute({
        route_date: routeDate,
        vehicle_id: vehicleId || null,
        origin_label: startPoint?.name ?? null,
        destination_label: endPoint?.name ?? null,
        notes: derived || null,
      });

      const allStops = [
        ...(startPoint ? [{ ...startPoint, order: 1 }] : []),
        ...stops.map((s, i) => ({ ...s, order: (startPoint ? 1 : 0) + i + 1 })),
        ...(endPoint ? [{ ...endPoint, order: (startPoint ? 1 : 0) + stops.length + 1 }] : []),
      ];

      for (const s of allStops) {
        await createRouteStop(route.id, {
          delivery_point_id: null,
          stop_order: s.order,
          gps_coordinates: { lat: s.lat, lng: s.lng },
        });
      }

      return route;
    },
    onSuccess: async (route) => {
      cancelBuilder();
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.stops(route.id) }),
      ]);
      onRouteCreated?.(route.id);
    },
    onError: (cause) => {
      onError(cause instanceof Error ? cause.message : "No se pudo guardar la ruta");
    },
  });

  return {
    phase,
    startPoint,
    endPoint,
    stops,
    routeDate,
    vehicleId,
    customName,
    editingRouteId,
    isSaving: saveMutation.isPending,
    setRouteDate,
    setVehicleId,
    setCustomName,
    handleMapClick,
    removeStart,
    removeEnd,
    removeStop,
    reorderStop,
    startNew,
    startEditing,
    cancelBuilder,
    save: saveMutation.mutate,
    handleMarkerDrag,
    addStopManual,
  };
}
