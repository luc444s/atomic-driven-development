from __future__ import annotations

from pathlib import Path

from importlib.metadata import entry_points


def ensure_installed_plugins(plugins_dir: Path) -> list[str]:
    """Enlaza en ``plugins_dir`` los plugins instalados vía entrypoint.

    El host descubre plugins por directorio (``*/plugin.json``). Los plugins
    empaquetados como ``systutor-tms`` se registran en el entrypoint
    ``systutor.plugins`` apuntando a su ``PLUGIN_ROOT``. Este puente crea un
    symlink ``<plugins_dir>/<id> -> PLUGIN_ROOT`` para que el loader existente
    los descubra sin modificar el kernel.

    Si ya existe un directorio real ``<plugins_dir>/<id>`` (plugin in-tree del
    monorepo), se respeta y no se sobreescribe.
    """
    plugins_dir.mkdir(parents=True, exist_ok=True)
    linked: list[str] = []
    try:
        eps = entry_points(group="systutor.plugins")
    except Exception:
        return linked

    for ep in eps:
        try:
            root = Path(ep.load())
        except Exception:
            continue
        if not root.is_dir():
            continue
        target = plugins_dir / ep.name
        if target.exists() or target.is_symlink():
            continue
        try:
            target.symlink_to(root, target_is_directory=True)
            linked.append(ep.name)
        except Exception:
            continue
    return linked
