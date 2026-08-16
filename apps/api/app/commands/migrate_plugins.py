from __future__ import annotations

import argparse
import sys

from sqlalchemy.orm import Session
from systutor.core.database import build_engine, build_session_factory
from systutor.kernel.plugins.migrations import upgrade_plugin_migrations
from systutor.kernel.plugins.persistent import (
    list_plugin_registry_records,
)
from systutor.kernel.plugins.runtime import PluginManifestRegistry

from apps.api.app.config import GasSettings as Settings


def run_plugin_migrations(
    db: Session,
    registry: PluginManifestRegistry,
    plugin_id: str | None = None,
) -> int:
    records = list_plugin_registry_records(db)
    if not records:
        print("No hay plugins registrados en la base de datos.")
        return 0

    if plugin_id:
        records = [r for r in records if r.plugin_id == plugin_id]
        if not records:
            print(f"Plugin '{plugin_id}' no encontrado en el registry.")
            return 1

    registry.discover()
    total = 0
    for record in records:
        if record.state != "enabled":
            print(f"  [{record.plugin_id}] saltado (estado: {record.state})")
            continue

        discovered = registry.get(record.plugin_id)
        if discovered is None:
            print(f"  [{record.plugin_id}] no encontrado en filesystem, saltado")
            continue

        current = record.migration_version or "(ninguna)"
        try:
            new_version = upgrade_plugin_migrations(
                db,
                record=record,
                discovered=discovered,
            )
            if new_version and new_version != record.migration_version:
                db.add(record)
                db.flush()
                print(f"  [{record.plugin_id}] {current} -> {new_version}")
                total += 1
            else:
                print(f"  [{record.plugin_id}] ya en última versión ({current})")
        except Exception as exc:
            print(f"  [{record.plugin_id}] ERROR: {exc}")

    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta migraciones de plugins")
    parser.add_argument(
        "plugin_id",
        nargs="?",
        default=None,
        help="Plugin específico (opcional, por defecto todos los habilitados)",
    )
    args = parser.parse_args()

    settings = Settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(settings)

    registry = PluginManifestRegistry(settings.plugins_dir)

    with session_factory() as db:
        migrated = run_plugin_migrations(db, registry, plugin_id=args.plugin_id)
        db.commit()

    engine.dispose()
    return 0 if migrated >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
