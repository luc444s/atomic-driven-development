from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from apps.api.app.core.errors import AppError
from apps.api.app.kernel.plugins.manifest import PluginManifest
from packages.sdk import PluginContext, PluginRegistration


class PluginRuntimeError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500, code="plugin_runtime_error")


@dataclass(slots=True)
class DiscoveredPlugin:
    manifest: PluginManifest
    root: Path


@dataclass(slots=True)
class LoadedPlugin:
    manifest: PluginManifest
    root: Path
    status: str
    registration: PluginRegistration | None = None
    error_message: str | None = None


class PluginManifestRegistry:
    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir
        self._plugins: dict[str, DiscoveredPlugin] = {}

    def discover(self) -> None:
        self._plugins.clear()

        if not self.plugins_dir.exists():
            return

        for manifest_path in sorted(self.plugins_dir.glob("*/plugin.json")):
            manifest = self._load_manifest(manifest_path)
            if manifest.id in self._plugins:
                raise PluginRuntimeError(f"Plugin duplicado detectado: {manifest.id}")
            self._plugins[manifest.id] = DiscoveredPlugin(
                manifest=manifest,
                root=manifest_path.parent,
            )

    def list(self) -> list[PluginManifest]:
        return [plugin.manifest for plugin in self.discovered()]

    def discovered(self) -> list[DiscoveredPlugin]:
        return [self._plugins[key] for key in sorted(self._plugins)]

    def get(self, plugin_id: str) -> DiscoveredPlugin | None:
        return self._plugins.get(plugin_id)

    @staticmethod
    def _load_manifest(manifest_path: Path) -> PluginManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return PluginManifest.model_validate(data)


class PluginRuntime:
    def __init__(self, registry: PluginManifestRegistry) -> None:
        self.registry = registry
        self._results: dict[str, LoadedPlugin] = {}

    def load(self, *, disabled_plugins: set[str] | None = None) -> None:
        disabled_plugins = disabled_plugins or set()
        ordered_plugins, cyclic_plugins = self._resolve_load_order()
        self._results.clear()

        for discovered in ordered_plugins:
            manifest = discovered.manifest
            if manifest.id in cyclic_plugins:
                self._results[manifest.id] = LoadedPlugin(
                    manifest=manifest,
                    root=discovered.root,
                    status="failed",
                    error_message="circular dependency detected",
                )
                continue

            if manifest.id in disabled_plugins:
                self._results[manifest.id] = LoadedPlugin(
                    manifest=manifest,
                    root=discovered.root,
                    status="disabled",
                )
                continue

            dependency_error = self._dependency_error(manifest)
            if dependency_error is not None:
                self._results[manifest.id] = LoadedPlugin(
                    manifest=manifest,
                    root=discovered.root,
                    status="failed",
                    error_message=dependency_error,
                )
                continue

            try:
                registration = self._load_registration(discovered)
                self._results[manifest.id] = LoadedPlugin(
                    manifest=manifest,
                    root=discovered.root,
                    status="enabled",
                    registration=registration,
                )
            except Exception as exc:
                self._results[manifest.id] = LoadedPlugin(
                    manifest=manifest,
                    root=discovered.root,
                    status="failed",
                    error_message=str(exc),
                )

    def list_results(self) -> list[LoadedPlugin]:
        if self._results:
            return [self._results[key] for key in sorted(self._results)]
        return [
            LoadedPlugin(manifest=plugin.manifest, root=plugin.root, status="discovered")
            for plugin in self.registry.discovered()
        ]

    def collect_event_handlers(self) -> dict[str, dict[str, list]]:
        handlers: dict[str, dict[str, list]] = {}
        for result in self.list_results():
            if result.status != "enabled" or result.registration is None:
                continue
            handlers[result.manifest.id] = result.registration.event_handlers
        return handlers

    def _dependency_error(self, manifest: PluginManifest) -> str | None:
        for dependency_id in manifest.requires:
            dependency = self._results.get(dependency_id)
            if dependency is None:
                return f"missing dependency: {dependency_id}"
            if dependency.status != "enabled":
                return f"dependency not enabled: {dependency_id}"
        return None

    def _resolve_load_order(self) -> tuple[list[DiscoveredPlugin], set[str]]:
        discovered = {plugin.manifest.id: plugin for plugin in self.registry.discovered()}
        indegree = {plugin_id: 0 for plugin_id in discovered}
        dependents: dict[str, list[str]] = {plugin_id: [] for plugin_id in discovered}

        for plugin_id, plugin in discovered.items():
            for dependency_id in plugin.manifest.requires:
                if dependency_id in discovered:
                    indegree[plugin_id] += 1
                    dependents[dependency_id].append(plugin_id)

        queue = sorted([plugin_id for plugin_id, degree in indegree.items() if degree == 0])
        ordered_ids: list[str] = []

        while queue:
            plugin_id = queue.pop(0)
            ordered_ids.append(plugin_id)
            for dependent_id in sorted(dependents[plugin_id]):
                indegree[dependent_id] -= 1
                if indegree[dependent_id] == 0:
                    queue.append(dependent_id)
                    queue.sort()

        cyclic_plugins = {plugin_id for plugin_id, degree in indegree.items() if degree > 0}
        remaining = sorted(cyclic_plugins)
        ordered_ids.extend(remaining)
        return [discovered[plugin_id] for plugin_id in ordered_ids], cyclic_plugins

    def _load_registration(self, discovered: DiscoveredPlugin) -> PluginRegistration:
        module_name, function_name = discovered.manifest.backend_entrypoint.split(":", 1)
        module = self._load_module(discovered, module_name)
        register = getattr(module, function_name, None)
        if register is None or not callable(register):
            raise PluginRuntimeError(
                "entrypoint invalido para plugin "
                f"{discovered.manifest.id}: {discovered.manifest.backend_entrypoint}"
            )

        context = PluginContext(discovered.manifest)
        register(context)
        if not context.registration.permissions:
            context.register_permissions(list(discovered.manifest.permissions))
        if not context.registration.events:
            context.register_events(list(discovered.manifest.events))
        return context.registration

    @staticmethod
    def _load_module(discovered: DiscoveredPlugin, module_name: str) -> ModuleType:
        module_path = discovered.root.joinpath(*module_name.split(".")).with_suffix(".py")
        if not module_path.exists():
            raise PluginRuntimeError(f"plugin module not found: {module_path}")

        import_name = f"systutor_plugin_{discovered.manifest.id}_{module_name.replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(import_name, module_path)
        if spec is None or spec.loader is None:
            raise PluginRuntimeError(f"cannot load plugin module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
