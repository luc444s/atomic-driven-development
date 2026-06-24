import type { PluginSidebarEntry } from "../plugins/runtime";

export type ShellNavLinkItem = {
  kind: "link";
  label: string;
  to: string;
};

export type ShellNavActionItem = {
  kind: "action";
  label: string;
  action: "logout";
};

export type ShellNavSection = {
  title: string;
  items: Array<ShellNavLinkItem | ShellNavActionItem>;
};

type BuildShellSidebarSectionsInput = {
  permissions: string[];
  pluginNavigation: PluginSidebarEntry[];
};

export function buildShellSidebarSections({
  permissions,
  pluginNavigation,
}: BuildShellSidebarSectionsInput): ShellNavSection[] {
  const sections: ShellNavSection[] = [
    {
      title: "Core",
      items: [{ kind: "link", label: "Dashboard", to: "/app/system" }],
    },
  ];

  if (permissions.includes("core.plugin.read")) {
    sections[0].items.push({ kind: "link", label: "Plugins", to: "/app/plugins" });
  }

  const settingsItems: Array<ShellNavLinkItem | ShellNavActionItem> = [];
  if (permissions.includes("core.users.read")) {
    settingsItems.push({ kind: "link", label: "Users", to: "/app/settings/users" });
  }
  if (permissions.includes("core.roles.read")) {
    settingsItems.push({ kind: "link", label: "Roles", to: "/app/settings/roles" });
  }
  if (permissions.includes("core.branches.manage")) {
    settingsItems.push({ kind: "link", label: "Branches", to: "/app/settings/branches" });
  }
  if (settingsItems.length > 0) {
    sections.push({ title: "Settings", items: settingsItems });
  }

  if (pluginNavigation.length > 0) {
    sections.push({
      title: "Plugins Enabled",
      items: pluginNavigation.map((entry) => ({
        kind: "link",
        label: entry.label,
        to: entry.to,
      })),
    });
  }

  sections.push({
    title: "Session",
    items: [{ kind: "action", label: "Logout", action: "logout" }],
  });

  return sections;
}
