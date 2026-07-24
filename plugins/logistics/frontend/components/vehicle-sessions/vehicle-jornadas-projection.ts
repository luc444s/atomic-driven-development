import type { LogisticsVehicle, VehicleSession } from "../../api";

export const PENDING_SESSION_STATUSES = new Set([
  "DRAFT",
]);

export const LIVE_SESSION_STATUSES = new Set([
  "LOADING",
  "READY_TO_DEPART",
  "OUTBOUND",
  "RETURNING",
  "AWAITING_RECONCILIATION",
]);

export const ACTIVE_SESSION_STATUSES = new Set([
  ...PENDING_SESSION_STATUSES,
  ...LIVE_SESSION_STATUSES,
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

function sortPendingSessions(sessions: VehicleSession[]) {
  return [...sessions].sort(
    (left, right) => new Date(left.opened_at).getTime() - new Date(right.opened_at).getTime()
  );
}

function sortHistoricalSessions(sessions: VehicleSession[]) {
  return [...sessions].sort(
    (left, right) => new Date(right.closed_at ?? right.opened_at).getTime() - new Date(left.closed_at ?? left.opened_at).getTime()
  );
}

function pickActiveSession(sessions: VehicleSession[]) {
  const liveSession = sessions.find((session) => LIVE_SESSION_STATUSES.has(session.status));
  if (liveSession) {
    return liveSession;
  }
  return sortPendingSessions(sessions.filter((session) => PENDING_SESSION_STATUSES.has(session.status)))[0] ?? null;
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
    const vehicleSessions = sessionsByVehicle.get(vehicle.id) ?? [];
    const activeSession = pickActiveSession(vehicleSessions);
    const pendingSessions = sortPendingSessions(
      vehicleSessions.filter(
        (session) => ACTIVE_SESSION_STATUSES.has(session.status) && session.id !== activeSession?.id
      )
    );
    return {
      vehicle_id: vehicle.id,
      vehicle_plate: vehicle.plate,
      vehicle_type: vehicle.vehicle_type,
      active_session: activeSession,
      pending_sessions: pendingSessions,
      historical_sessions: sortHistoricalSessions(vehicleSessions.filter((session) => session.status === "CLOSED")),
      latest_session_status: sortHistoricalSessions(vehicleSessions)[0]?.status ?? null,
    };
  });

  for (const session of sessions) {
    if (cards.some((card) => card.vehicle_id === session.vehicle_id)) {
      continue;
    }
    const vehicleSessions = sessionsByVehicle.get(session.vehicle_id) ?? [];
    const activeSession = pickActiveSession(vehicleSessions);
    cards.push({
      vehicle_id: session.vehicle_id,
      vehicle_plate: session.vehicle_plate,
      vehicle_type: null,
      active_session: activeSession,
      pending_sessions: sortPendingSessions(
        vehicleSessions.filter(
          (item) => ACTIVE_SESSION_STATUSES.has(item.status) && item.id !== activeSession?.id
        )
      ),
      historical_sessions: sortHistoricalSessions(vehicleSessions.filter((item) => item.status === "CLOSED")),
      latest_session_status: sortHistoricalSessions(vehicleSessions)[0]?.status ?? null,
    });
  }

  return cards.sort((left, right) => left.vehicle_plate.localeCompare(right.vehicle_plate));
}
