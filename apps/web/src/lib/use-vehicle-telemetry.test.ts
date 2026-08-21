import { describe, expect, it } from "vitest";

import { buildVehicleLocationPayload, positionsDiffer } from "./use-vehicle-telemetry";

function makeCoords(overrides: Partial<GeolocationCoordinates> = {}): GeolocationCoordinates {
  return {
    latitude: -12.046374,
    longitude: -77.042793,
    altitude: null,
    accuracy: 8,
    altitudeAccuracy: null,
    heading: 90,
    speed: 34.5,
    toJSON: () => ({}),
    ...overrides,
  };
}

function makePosition(overrides: Partial<GeolocationPosition> = {}): GeolocationPosition {
  return {
    coords: makeCoords(),
    timestamp: 1755800000000,
    ...overrides,
  } as GeolocationPosition;
}

describe("buildVehicleLocationPayload", () => {
  it("mapea coordenadas, precisión, velocidad y rumbo al payload", () => {
    const payload = buildVehicleLocationPayload(makePosition());
    expect(payload).toMatchObject({
      lat: -12.046374,
      lng: -77.042793,
      speed: 34.5,
      heading: 90,
      accuracy_meters: 8,
      source: "WEB",
    });
    expect(payload.recorded_at).toBe("2025-08-21T18:13:20.000Z");
  });

  it("serializa recorded_at desde el timestamp de captura", () => {
    const position = makePosition({ timestamp: 1755800123456 });
    const payload = buildVehicleLocationPayload(position);
    expect(payload.recorded_at).toBe(new Date(1755800123456).toISOString());
  });

  it("redondea speed/heading/accuracy a 2 decimales", () => {
    const position = makePosition({
      coords: makeCoords({
        accuracy: 8.4567,
        heading: 89.9999,
        speed: 34.555,
      }),
    });
    const payload = buildVehicleLocationPayload(position);
    expect(payload.speed).toBe(34.55);
    expect(payload.heading).toBe(90);
    expect(payload.accuracy_meters).toBe(8.46);
  });
});

describe("positionsDiffer", () => {
  it("reporta la primera posición siempre", () => {
    const payload = buildVehicleLocationPayload(makePosition());
    expect(positionsDiffer(null, payload)).toBe(true);
  });

  it("no reporta posiciones idénticas (dedup local)", () => {
    const payload = buildVehicleLocationPayload(makePosition());
    expect(positionsDiffer(payload, { ...payload })).toBe(false);
  });

  it("reporta cuando cambia lat/lng aunque el resto sea igual", () => {
    const first = buildVehicleLocationPayload(makePosition());
    const second = buildVehicleLocationPayload(
      makePosition({
        coords: makeCoords({
          latitude: -12.05,
          longitude: -77.05,
        }),
      })
    );
    expect(positionsDiffer(first, second)).toBe(true);
  });
});