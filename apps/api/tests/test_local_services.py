from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_MODULE_PATH = Path(__file__).resolve().parents[3] / "tools" / "dev" / "local_services.py"
_SPEC = spec_from_file_location("test_local_services_module", _MODULE_PATH)
assert _SPEC and _SPEC.loader
local_services = module_from_spec(_SPEC)
_SPEC.loader.exec_module(local_services)


def test_ensure_postgres_started_reuses_existing_local_server(
    monkeypatch, capsys
) -> None:
    started_commands: list[list[str]] = []

    monkeypatch.setattr(local_services, "postgres_running", lambda: False)
    monkeypatch.setattr(local_services, "postgres_accepting_connections", lambda host, port: True)
    monkeypatch.setattr(
        local_services,
        "ensure_postgres_cluster",
        lambda: (_ for _ in ()).throw(AssertionError("should not init local cluster")),
    )
    monkeypatch.setattr(
        local_services,
        "run_command",
        lambda command, env=None: started_commands.append(command),
    )

    local_services.ensure_postgres_started(
        "postgresql+psycopg://postgres:postgres@localhost:5432/systutor"
    )

    assert started_commands == []
    assert "se reutiliza la instancia existente" in capsys.readouterr().out


def test_ensure_postgres_started_skips_remote_database_hosts(monkeypatch) -> None:
    monkeypatch.setattr(
        local_services,
        "ensure_postgres_cluster",
        lambda: (_ for _ in ()).throw(AssertionError("should not init remote database")),
    )
    monkeypatch.setattr(
        local_services,
        "run_command",
        lambda command, env=None: (_ for _ in ()).throw(AssertionError("should not start remote database")),
    )

    local_services.ensure_postgres_started(
        "postgresql+psycopg://postgres:postgres@db.example.com:5432/systutor"
    )


def test_ensure_role_and_database_uses_database_url_credentials(monkeypatch) -> None:
    recorded_commands: list[list[str]] = []

    def fake_capture(command: list[str]) -> str:
        recorded_commands.append(command)
        if "pg_roles" in command[-1]:
            return "1"
        return "1"

    monkeypatch.setattr(local_services, "capture_command", fake_capture)
    monkeypatch.setattr(
        local_services,
        "run_command",
        lambda command, env=None: (_ for _ in ()).throw(AssertionError("should not create existing role/db")),
    )

    local_services.ensure_role_and_database(
        "postgresql+psycopg://postgres:postgres@localhost:5432/systutor"
    )

    assert recorded_commands
    assert recorded_commands[0][1] == "postgresql://postgres:postgres@localhost:5432/postgres"
