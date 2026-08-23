import { useCallback, useEffect, useRef, useState } from "react";
import { reportVehicleLocation, type VehicleLocationRecordPayload } from "../../../../plugins/logistics/frontend/api/route-control";

export type TelemetryStatus = "idle" | "running" | "error";

export type VehicleTelemetrySnapshot = {
  status: TelemetryStatus;
  lastLat: number | null;
  lastLng: number | null;
  lastAccuracy: number | null;
  lastReportedAt: string | null;
  error: string | null;
};

export function buildVehicleLocationPayload(position: GeolocationPosition): VehicleLocationRecordPayload {
  const coords = position.coords;
  return {
    lat: coords.latitude,
    lng: coords.longitude,
    speed: coords.speed != null ? Number(coords.speed.toFixed(2)) : null,
    heading: coords.heading != null ? Number(coords.heading.toFixed(2)) : null,
    accuracy_meters: coords.accuracy != null ? Number(coords.accuracy.toFixed(2)) : null,
    recorded_at: new Date(position.timestamp).toISOString(),
    source: "WEB",
  };
}

export function positionsDiffer(
  previous: VehicleLocationRecordPayload | null,
  next: VehicleLocationRecordPayload
): boolean {
  if (previous === null) {
    return true;
  }
  return previous.lat !== next.lat || previous.lng !== next.lng;
}

const DEFAULT_INTERVAL_MS = 5000;

export function useVehicleTelemetry(
  sessionId: string,
  options: { intervalMs?: number } = {}
) {
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS;
  const [status, setStatus] = useState<TelemetryStatus>("idle");
  const [lastLat, setLastLat] = useState<number | null>(null);
  const [lastLng, setLastLng] = useState<number | null>(null);
  const [lastAccuracy, setLastAccuracy] = useState<number | null>(null);
  const [lastReportedAt, setLastReportedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const watchIdRef = useRef<number | null>(null);
  const timerRef = useRef<number | null>(null);
  const pendingRef = useRef<VehicleLocationRecordPayload | null>(null);
  const lastSentRef = useRef<VehicleLocationRecordPayload | null>(null);
  const sessionIdRef = useRef(sessionId);
  sessionIdRef.current = sessionId;

  const flush = useCallback(async () => {
    const pending = pendingRef.current;
    if (pending === null) {
      return;
    }
    pendingRef.current = null;
    try {
      await reportVehicleLocation(sessionIdRef.current, pending);
      lastSentRef.current = pending;
      setLastReportedAt(pending.recorded_at);
      setError(null);
    } catch (cause) {
      pendingRef.current = pending;
      setError(cause instanceof Error ? cause.message : "No se pudo reportar la ubicación");
    }
  }, []);

  const handlePosition = useCallback(
    (position: GeolocationPosition) => {
      const payload = buildVehicleLocationPayload(position);
      setLastLat(payload.lat);
      setLastLng(payload.lng);
      setLastAccuracy(payload.accuracy_meters ?? null);
      if (positionsDiffer(lastSentRef.current, payload)) {
        pendingRef.current = payload;
      }
    },
    []
  );

  const handleError = useCallback((cause: GeolocationPositionError) => {
    setStatus("error");
    setError(cause.message ?? "Permiso de ubicación denegado o geo no disponible");
  }, []);

  const start = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setStatus("error");
      setError("Este navegador no soporta geolocalización");
      return;
    }
    if (typeof window !== "undefined" && !window.isSecureContext) {
      setStatus("error");
      setError(
        "La geolocalización requiere origen seguro (HTTPS o localhost). " +
          "Accedé vía HTTPS o habilitá el flag unsafely-treat-insecure-origin-as-secure."
      );
      return;
    }
    if (watchIdRef.current !== null) {
      return;
    }
    setError(null);
    watchIdRef.current = navigator.geolocation.watchPosition(
      handlePosition,
      handleError,
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 }
    );
    timerRef.current = window.setInterval(flush, intervalMs);
    setStatus("running");
  }, [flush, handleError, handlePosition, intervalMs]);

  const stop = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    pendingRef.current = null;
    setStatus("idle");
  }, []);

  useEffect(() => stop, [stop]);

  const snapshot: VehicleTelemetrySnapshot = {
    status,
    lastLat,
    lastLng,
    lastAccuracy,
    lastReportedAt,
    error,
  };

  return { snapshot, start, stop };
}