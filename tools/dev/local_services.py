from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = Path.home() / ".postgresql"
DEFAULT_LOG_FILE = DEFAULT_DATA_DIR / "postgres.log"


def read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(read_env_file(PROJECT_ROOT / ".env"))
    return env


def get_database_url(env: dict[str, str]) -> str:
    return env.get(
        "SYSTUTOR_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/systutor",
    )


def normalize_postgres_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def ensure_postgres_cluster() -> None:
    if DEFAULT_DATA_DIR.exists():
        return

    run_command(["initdb", "-D", str(DEFAULT_DATA_DIR), "--auth=trust"])


def postgres_running() -> bool:
    result = subprocess.run(
        ["pg_ctl", "-D", str(DEFAULT_DATA_DIR), "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def ensure_postgres_started() -> None:
    ensure_postgres_cluster()
    if postgres_running():
        return

    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "pg_ctl",
            "-D",
            str(DEFAULT_DATA_DIR),
            "-l",
            str(DEFAULT_LOG_FILE),
            "-o",
            "-p 5432 -h 127.0.0.1",
            "start",
        ]
    )


def ensure_role_and_database(database_url: str) -> None:
    parsed = urlparse(normalize_postgres_url(database_url))
    username = parsed.username or "postgres"
    password = parsed.password or "postgres"
    database = parsed.path.lstrip("/") or "systutor"
    bootstrap_url = "postgresql://127.0.0.1:5432/postgres"

    role_exists = capture_command(
        [
            "psql",
            bootstrap_url,
            "-tAc",
            f"SELECT 1 FROM pg_roles WHERE rolname = {quote_sql(username)};",
        ]
    ).strip()
    if role_exists != "1":
        run_command(
            [
                "psql",
                bootstrap_url,
                "-c",
                (
                    f"CREATE ROLE {quote_ident(username)} WITH LOGIN SUPERUSER "
                    f"PASSWORD {quote_sql(password)};"
                ),
            ]
        )

    database_exists = capture_command(
        [
            "psql",
            bootstrap_url,
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname = {quote_sql(database)};",
        ]
    ).strip()
    if database_exists != "1":
        run_command(
            [
                "psql",
                bootstrap_url,
                "-c",
                f"CREATE DATABASE {quote_ident(database)} OWNER {quote_ident(username)};",
            ]
        )


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def quote_sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def run_command(command: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def capture_command(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def start_backend(env: dict[str, str]) -> None:
    python_bin = PROJECT_ROOT / ".venv" / "bin" / "python"
    if not python_bin.exists():
        raise SystemExit(
            "No se encontro .venv/bin/python. Ejecuta primero: python3 -m pip install -e \".[dev]\""
        )

    os.execve(
        str(python_bin),
        [
            str(python_bin),
            "-m",
            "uvicorn",
            "apps.api.app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        env,
    )


def open_psql(env: dict[str, str]) -> None:
    database_url = normalize_postgres_url(get_database_url(env))
    os.execvpe("psql", ["psql", database_url], env)


def stop_postgres() -> None:
    if not postgres_running():
        print("PostgreSQL no estaba corriendo.")
        return
    run_command(["pg_ctl", "-D", str(DEFAULT_DATA_DIR), "stop"])
    print("PostgreSQL detenido.")


def stop_backend() -> None:
    import signal

    result = subprocess.run(
        ["pgrep", "-f", "uvicorn apps.api.app.main"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0:
        for pid_str in result.stdout.strip().splitlines():
            try:
                pid = int(pid_str)
                os.kill(pid, signal.SIGTERM)
                print(f"Backend detenido (pid={pid})")
            except (OSError, ValueError):
                pass
    else:
        print("Backend no estaba corriendo.")


def redis_running() -> bool:
    result = subprocess.run(
        ["redis-cli", "ping"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() == "PONG"


def ensure_redis_started() -> None:
    if redis_running():
        return
    run_command(["redis-server", "--daemonize", "yes"])
    print("Redis iniciado en 127.0.0.1:6379")


def stop_redis() -> None:
    if not redis_running():
        return
    run_command(["redis-cli", "shutdown"])
    print("Redis detenido.")


def stop_services() -> None:
    stop_backend()
    stop_redis()
    stop_postgres()


def print_status(env: dict[str, str]) -> None:
    database_url = normalize_postgres_url(get_database_url(env))
    print(f"postgres_data_dir={DEFAULT_DATA_DIR}")
    print(f"postgres_running={postgres_running()}")
    print(f"redis_running={redis_running()}")
    print(f"database_url={database_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local services helper for SYSTUTOR OSS")
    parser.add_argument(
        "command",
        choices=["postgres", "backend", "services", "stop", "psql", "status"],
        help="Command to execute",
    )
    args = parser.parse_args()

    env = build_runtime_env()
    database_url = get_database_url(env)

    if args.command in {"postgres", "backend", "services", "psql"}:
        ensure_postgres_started()
        ensure_role_and_database(database_url)

    if args.command in {"backend", "services"}:
        ensure_redis_started()

    if args.command == "postgres":
        print("PostgreSQL local listo en 127.0.0.1:5432")
        return

    if args.command == "backend":
        start_backend(env)

    if args.command == "services":
        start_backend(env)

    if args.command == "psql":
        open_psql(env)

    if args.command == "stop":
        stop_services()
        return

    if args.command == "status":
        print_status(env)


if __name__ == "__main__":
    main()
