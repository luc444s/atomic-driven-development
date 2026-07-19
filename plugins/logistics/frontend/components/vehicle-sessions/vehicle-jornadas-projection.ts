import type { LogisticsVehicle, VehicleSession } from "../../api";

export const ACTIVE_SESSION_STATUSES = new Set([
  "DRAFT",
  "LOADING",
  "READY_TO_DEPART",
  "OUTBOUND",
  "RETURNING",
  "AWAITING_RECONCILIATION",
]);

export type VehicleProjectionCard = {
  vehicle_id: string;
  vehicle_plate: string;
  vehicle_type: string | null;
  active_session: VehicleSession | null;
  pending_sessions: VehicleSession[];
  historical_sessions: VehicleSession[];
  latest_session_status: string | null;
};

function sortSessionsByRecency(sessions: VehicleSession[]) {
  return [...sessions].sort(
    (left, right) => new Date(right.opened_at).getTime() - new Date(left.opened_at).getTime()
  );
}

export function buildVehicleProjectionCards(
  vehicles: LogisticsVehicle[],
  sessions: VehicleSession[]
): VehicleProjectionCard[] {
  const sessionsByVehicle = new Map<string, VehicleSession[]>();
  for (const session of sessions) {
    const current = sessionsByVehicle.get(session.vehicle_id) ?? [];
    current.push(session);
    sessionsByVehicle.set(session.vehicle_id, current);
  }

  const cards = vehicles.map((vehicle) => {
    const vehicleSessions = sortSessionsByRecency(sessionsByVehicle.get(vehicle.id) ?? []);
    const activeSession =
      vehicleSessions.find((session) => ACTIVE_SESSION_STATUSES.has(session.status)) ?? null;
    return {
      vehicle_id: vehicle.id,
      vehicle_plate: vehicle.plate,
      vehicle_type: vehicle.vehicle_type,
      active_session: activeSession,
      pending_sessions: vehicleSessions.filter(
        (session) => ACTIVE_SESSION_STATUSES.has(session.status) && session.id !== activeSession?.id
      ),
      historical_sessions: vehicleSessions.filter((session) => session.status === "CLOSED"),
      latest_session_status: vehicleSessions[0]?.status ?? null,
    };
  });

  for (const session of sessions) {
    if (cards.some((card) => card.vehicle_id === session.vehicle_id)) {
      continue;
    }
    const vehicleSessions = sortSessionsByRecency(sessionsByVehicle.get(session.vehicle_id) ?? []);
    const activeSession =
      vehicleSessions.find((item) => ACTIVE_SESSION_STATUSES.has(item.status)) ?? null;
    cards.push({
      vehicle_id: session.vehicle_id,
      vehicle_plate: session.vehicle_plate,
      vehicle_type: null,
      active_session: activeSession,
      pending_sessions: vehicleSessions.filter(
        (item) => ACTIVE_SESSION_STATUSES.has(item.status) && item.id !== activeSession?.id
      ),
      historical_sessions: vehicleSessions.filter((item) => item.status === "CLOSED"),
      latest_session_status: vehicleSessions[0]?.status ?? null,
    });
  }

  return cards.sort((left, right) => left.vehicle_plate.localeCompare(right.vehicle_plate));
}
