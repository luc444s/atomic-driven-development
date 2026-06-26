import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { clearClientSession, hasValidTenantContext } from "../auth/session";
import { useAuthStore } from "../auth/store";
import { shouldRedirectToLogin } from "../auth/RequireAuth";
import { ShellHeader } from "../../shared/layout/ShellHeader";
import { buildShellSidebarSections } from "./navigation";
import type { PluginRuntimeRecord } from "../../shared/api/client";
import type { UserProfile } from "../auth/api";

const demoUser: UserProfile = {
  id: "user-1",
  tenant_id: "tenant-1",
  tenant_name: "Solygas Espana",
  branch_id: "branch-1",
  branch_name: "Madrid",
  email: "admin@solygas.com",
  full_name: "Admin Solygas",
  is_active: true,
  is_superadmin: false,
  permissions: [
    "core.users.read",
    "core.roles.read",
    "core.branches.read",
    "core.plugin.runtime.read",
    "logistics.delivery.read",
  ],
};

const enabledPluginRecord: PluginRuntimeRecord = {
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
  created_at: "2026-06-24T00:00:00Z",
  updated_at: "2026-06-24T00:00:00Z",
};

describe("tenant-specific shell", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it("hydrates tenant context after login bootstrap", () => {
    const store = useAuthStore.getState();

    store.setSession("token-demo");
    store.hydrateUserContext(demoUser);
    store.setPluginRuntime([enabledPluginRecord]);

    const hydrated = useAuthStore.getState();

    expect(hydrated.token).toBe("token-demo");
    expect(hydrated.user?.email).toBe("admin@solygas.com");
    expect(hydrated.currentTenant).toEqual({ id: "tenant-1", name: "Solygas Espana" });
    expect(hydrated.currentBranch).toEqual({ id: "branch-1", name: "Madrid" });
    expect(hydrated.permissions).toEqual(demoUser.permissions);
    expect(hydrated.enabledPlugins.map((plugin) => plugin.plugin_id)).toEqual(["logistics"]);
    expect(hydrated.isSuperadmin).toBe(false);
  });

  it("renders tenant header with tenant branch and user", () => {
    const markup = renderToStaticMarkup(
      <ShellHeader
        tenantName="Solygas Espana"
        branchName="Madrid"
        userName="Admin Solygas"
        userEmail="admin@solygas.com"
      />
    );

    expect(markup).toContain("Tenant:");
    expect(markup).toContain("Solygas Espana");
    expect(markup).toContain("Branch:");
    expect(markup).toContain("Madrid");
    expect(markup).toContain("User:");
    expect(markup).toContain("Admin Solygas");
  });

  it("hides sidebar items when permissions are missing", () => {
    const sections = buildShellSidebarSections({
      permissions: ["core.plugin.runtime.read"],
      pluginNavigation: [],
    });

    const labels = sections.flatMap((section) => section.items.map((item) => item.label));

    expect(labels).toContain("Dashboard");
    expect(labels).toContain("Plugins");
    expect(labels).not.toContain("Users");
    expect(labels).not.toContain("Roles");
    expect(labels).not.toContain("Branches");
  });

  it("clears stores on logout", () => {
    const store = useAuthStore.getState();

    store.setSession("token-demo");
    store.hydrateUserContext(demoUser);
    store.setPluginRuntime([enabledPluginRecord]);
    store.logout();

    const cleared = useAuthStore.getState();

    expect(cleared.token).toBeNull();
    expect(cleared.user).toBeNull();
    expect(cleared.currentTenant).toBeNull();
    expect(cleared.currentBranch).toBeNull();
    expect(cleared.permissions).toEqual([]);
    expect(cleared.enabledPlugins).toEqual([]);
    expect(cleared.pluginRuntimeRecords).toEqual([]);
  });

  it("redirects protected routes when token is missing", () => {
    expect(shouldRedirectToLogin(null)).toBe(true);
    expect(shouldRedirectToLogin("token-demo")).toBe(false);
  });

  it("invalidates session when token becomes invalid", () => {
    const queryClient = {
      clear: vi.fn(),
    };

    const store = useAuthStore.getState();
    store.setSession("token-demo");
    store.hydrateUserContext(demoUser);
    store.setPluginRuntime([enabledPluginRecord]);

    clearClientSession(queryClient as never);

    expect(queryClient.clear).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("detects invalid tenant context payloads", () => {
    expect(hasValidTenantContext(demoUser)).toBe(true);
    expect(
      hasValidTenantContext({
        ...demoUser,
        tenant_name: "",
      })
    ).toBe(false);
  });
});
