import { beforeEach, describe, expect, it, vi } from "vitest";

const apiRequestMock = vi.fn();

vi.mock("@systutor/shell/api/client", () => ({
  apiRequest: (...args: unknown[]) => apiRequestMock(...args),
}));

import {
  getRouteControlState,
  getVehicleLocationHistory,
  postRouteStopArrive,
  postRouteStopDepart,
  reportVehicleLocation,
} from "../../../../plugins/logistics/frontend/api/route-control";

describe("route-control fetchers", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("lee control-state del path correcto", async () => {
    apiRequestMock.mockResolvedValue({});
    await getRouteControlState("session-1");
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/control-state"
    );
  });

  it("lee location-history con query params", async () => {
    apiRequestMock.mockResolvedValue([]);
    await getVehicleLocationHistory("session-1", { from: "2026-01-01T00:00:00Z", limit: 50 });
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/location-history?from=2026-01-01T00%3A00%3A00Z&limit=50"
    );
  });

  it("omite query params vacíos en location-history", async () => {
    apiRequestMock.mockResolvedValue([]);
    await getVehicleLocationHistory("session-1", {});
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/location-history"
    );
  });

  it("reporta ubicación por POST con payload", async () => {
    apiRequestMock.mockResolvedValue({});
    await reportVehicleLocation("session-1", {
      lat: -12.04,
      lng: -77.04,
      recorded_at: "2026-01-01T10:00:00Z",
      source: "WEB",
    });
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/location",
      {
        method: "POST",
        body: JSON.stringify({
          lat: -12.04,
          lng: -77.04,
          recorded_at: "2026-01-01T10:00:00Z",
          source: "WEB",
        }),
      }
    );
  });

  it("postea arrive y depart en los paths de parada", async () => {
    apiRequestMock.mockResolvedValue({});
    await postRouteStopArrive("session-1", "stop-1");
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/stops/stop-1/arrive",
      { method: "POST" }
    );
    await postRouteStopDepart("session-1", "stop-1");
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/plugins/logistics/vehicle-sessions/session-1/stops/stop-1/depart",
      { method: "POST" }
    );
  });
});