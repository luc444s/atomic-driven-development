import { describe, expect, it } from "vitest";

import { hasRequiredPermissions } from "../shell/permissions";
import { buildFrontendPluginRuntime, listFrontendPluginRegistrations } from "./runtime";
import type { PluginRuntimeRecord } from "../../shared/api/client";

const enabledLogisticsRecord: PluginRuntimeRecord = {
  id: "plugin-runtime-1",
  plugin_id: "logistics",
  name: "Logistics",
  version: "0.1.0",
  api_version: "1",
  state: "enabled",
  is_enabled: true,
  backend_entrypoint: "backend.plugin:register",
  frontend_entrypoint: "frontend/register.ts",
  requires_json: [],
  permissions_json: ["logistics.delivery.read"],
  events_json: ["logistics.delivery.created"],
  description: "Plugin Logistics",
  migration_version: null,
  installed_at: null,
  enabled_at: null,
  disabled_at: null,
  last_error: null,
  created_at: "2026-06-23T00:00:00Z",
  updated_at: "2026-06-23T00:00:00Z",
};

describe("frontend plugin runtime", () => {
  it("registers plugin routes, navigation and widgets", () => {
    const registrations = listFrontendPluginRegistrations();
    const logistics = registrations.find((registration) => registration.pluginId === "logistics");

    expect(logistics).toBeDefined();
    expect(logistics?.routes.map((route) => route.path)).toEqual(["logistics"]);
    expect(logistics?.navigation.map((item) => item.to)).toEqual(["/app/logistics"]);
    expect(logistics?.widgets.map((widget) => widget.id)).toEqual([
      "logistics.runtime.summary",
    ]);
  });

  it("shows enabled plugin features when permissions match", () => {
    const runtime = buildFrontendPluginRuntime({
      records: [enabledLogisticsRecord],
      registrations: listFrontendPluginRegistrations(),
      userPermissions: ["logistics.delivery.read"],
    });

    expect(runtime.routes.some((route) => route.pluginId === "logistics")).toBe(true);
    expect(runtime.navigation.some((entry) => entry.pluginId === "logistics")).toBe(true);
    expect(runtime.widgets.some((widget) => widget.pluginId === "logistics")).toBe(true);
  });

  it("hides disabled plugin frontend entries", () => {
    const runtime = buildFrontendPluginRuntime({
      records: [{ ...enabledLogisticsRecord, state: "disabled", is_enabled: false }],
      registrations: listFrontendPluginRegistrations(),
      userPermissions: ["logistics.delivery.read"],
    });

    expect(runtime.routes).toHaveLength(0);
    expect(runtime.navigation).toHaveLength(0);
    expect(runtime.widgets).toHaveLength(0);
  });

  it("protects plugin frontend entries when permission is missing", () => {
    const runtime = buildFrontendPluginRuntime({
      records: [enabledLogisticsRecord],
      registrations: listFrontendPluginRegistrations(),
      userPermissions: [],
    });

    expect(runtime.routes).toHaveLength(0);
    expect(runtime.navigation).toHaveLength(0);
    expect(runtime.widgets).toHaveLength(0);
  });

  it("evaluates required permissions explicitly", () => {
    expect(hasRequiredPermissions([], undefined)).toBe(true);
    expect(hasRequiredPermissions(["logistics.delivery.read"], ["logistics.delivery.read"])).toBe(
      true
    );
    expect(hasRequiredPermissions([], ["logistics.delivery.read"])).toBe(false);
  });
});
