import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import {
  BranchesPageContent,
} from "../settings/BranchesPage";
import { PluginsPageContent } from "../system/PluginsPage";
import { RolesPageContent } from "../settings/RolesPage";
import { UsersPageContent } from "../settings/UsersPage";
import {
  coreManagementKeys,
  invalidateCoreManagementKey,
  invalidatePluginRuntimeCaches,
} from "./api";
import { buildShellSidebarSections } from "../shell/navigation";

const users = [
  {
    id: "user-1",
    tenant_id: "tenant-1",
    branch_id: "branch-1",
    name: "Admin Core",
    email: "admin@example.com",
    active: true,
    category: null,
    roles: ["admin"],
    created_at: "2026-06-25T00:00:00Z",
    updated_at: "2026-06-25T00:00:00Z",
  },
];

const roles = [
  {
    id: "role-1",
    tenant_id: "tenant-1",
    name: "admin",
    permissions: ["core.users.read", "core.roles.read"],
    active: true,
    created_at: "2026-06-25T00:00:00Z",
    updated_at: "2026-06-25T00:00:00Z",
  },
];

const branches = [
  {
    id: "branch-1",
    tenant_id: "tenant-1",
    name: "Main",
    code: "MAIN",
    active: true,
    created_at: "2026-06-25T00:00:00Z",
    updated_at: "2026-06-25T00:00:00Z",
  },
];

const permissions = [
  {
    id: "permission-1",
    name: "core.users.read",
    description: "Users read",
    created_at: "2026-06-25T00:00:00Z",
  },
];

const plugins = [
  {
    id: "plugin-1",
    plugin_id: "logistics",
    name: "Logistics",
    version: "0.1.0",
    api_version: "1",
    state: "disabled",
    is_enabled: false,
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
    created_at: "2026-06-25T00:00:00Z",
    updated_at: "2026-06-25T00:00:00Z",
  },
];

describe("core management frontend", () => {
  it("renders users page content", () => {
    const markup = renderToStaticMarkup(
      <UsersPageContent
        users={users}
        roles={roles}
        branches={branches}
        categories={[]}
        canCreate
        canUpdate
        canDisable
        isDialogOpen={false}
        formState={{ name: "", email: "", password: "", branch_id: "", category: "", role_ids: [] }}
        formError={null}
        isSaving={false}
        isToggling={false}
        hasError={false}
        onCreate={() => undefined}
        onEdit={() => undefined}
        onCloseDialog={() => undefined}
        onSubmit={() => undefined}
        onFieldChange={() => undefined}
        onToggleUser={() => undefined}
      />
    );

    expect(markup).toContain("Usuarios");
    expect(markup).toContain("Admin Core");
    expect(markup).toContain("admin@example.com");
  });

  it("renders roles page content", () => {
    const markup = renderToStaticMarkup(
      <RolesPageContent
        roles={roles}
        permissions={permissions}
        canManage
        hasError={false}
        isDialogOpen={false}
        formState={{ name: "", permission_names: [] }}
        formError={null}
        isSaving={false}
        onCreate={() => undefined}
        onEdit={() => undefined}
        onCloseDialog={() => undefined}
        onSubmit={() => undefined}
        onFieldChange={() => undefined}
        onToggleRole={() => undefined}
      />
    );

    expect(markup).toContain("Roles");
    expect(markup).toContain("admin");
  });

  it("renders branches page content", () => {
    const markup = renderToStaticMarkup(
      <BranchesPageContent
        branches={branches}
        canManage
        hasError={false}
        isDialogOpen={false}
        formState={{ name: "", code: "" }}
        formError={null}
        isSaving={false}
        onCreate={() => undefined}
        onEdit={() => undefined}
        onCloseDialog={() => undefined}
        onSubmit={() => undefined}
        onFieldChange={() => undefined}
        onToggleBranch={() => undefined}
      />
    );

    expect(markup).toContain("Sucursales");
    expect(markup).toContain("Main");
  });

  it("renders plugins page content and hides admin actions without permission", () => {
    const markup = renderToStaticMarkup(
      <PluginsPageContent
        plugins={plugins}
        frontendRuntime={{
          isLoading: false,
          error: null,
          registrations: [],
          recordsById: new Map(),
          routes: [],
          navigation: [],
          widgets: [],
        }}
        canManage={false}
        hasError={false}
        isMutating={false}
        onAction={() => undefined}
      />
    );

    expect(markup).toContain("Plugins");
    expect(markup).toContain("Logistics");
    expect(markup).toContain("Solo lectura");
    expect(markup).not.toContain(">Instalar<");
  });

  it("hides users, roles and branches menu items without read permissions", () => {
    const sections = buildShellSidebarSections({
      permissions: ["core.plugin.runtime.read"],
      pluginNavigation: [],
    });
    const labels = sections.flatMap((section) => section.items.map((item) => item.label));

    expect(labels).not.toContain("Usuarios");
    expect(labels).not.toContain("Roles");
    expect(labels).not.toContain("Sucursales");
    expect(labels).toContain("Plugins");
  });

  it("refreshes users table by invalidating the users query key", async () => {
    const queryClient = {
      invalidateQueries: vi.fn().mockResolvedValue(undefined),
    };

    await invalidateCoreManagementKey(queryClient as never, coreManagementKeys.users);

    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: [...coreManagementKeys.users],
    });
  });

  it("refreshes plugin runtime caches after admin actions", async () => {
    const queryClient = {
      invalidateQueries: vi.fn().mockResolvedValue(undefined),
    };

    await invalidatePluginRuntimeCaches(queryClient as never);

    expect(queryClient.invalidateQueries).toHaveBeenCalledTimes(2);
  });
});
