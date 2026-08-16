"""Benchmark de endpoints criticos de logistics (SPEC 0049/0050).

Mide tiempo de pared y conteo de queries contra la base de datos dev.
Sin dependencias extra: usa el contador de eventos de SQLAlchemy.

Uso:
    .venv/bin/python tools/dev/benchmark_logistics.py [--iterations N]

Salida: tabla con min/avg, queries y sesiones.
"""
from __future__ import annotations

import argparse
import time
from collections.abc import Callable

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from plugins.logistics.backend.services.route_context import build_route_context
from plugins.logistics.backend.services.session_console import build_session_console_context
from plugins.logistics.backend.services.sessions import list_vehicle_sessions
from plugins.logistics.backend.services.snapshots import build_session_list_items


class QueryCounter:
    def __init__(self, engine) -> None:
        self.count = 0
        event.listen(engine, "after_cursor_execute", self._on_execute)

    def _on_execute(self, *args, **kwargs) -> None:
        self.count += 1

    def reset(self) -> None:
        self.count = 0


def _measure(
    counter: QueryCounter,
    fn: Callable[[], object],
    *,
    iterations: int,
) -> dict[str, float]:
    times: list[float] = []
    queries: list[int] = []
    for _ in range(iterations):
        counter.reset()
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
        queries.append(counter.count)
    return {
        "min_ms": min(times) * 1000,
        "avg_ms": sum(times) / len(times) * 1000,
        "queries": queries[-1],
    }


def run_benchmarks(iterations: int) -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    counter = QueryCounter(engine)

    with Session(engine) as db:
        tenant_id = str(
            db.execute(text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")).scalar_one()
        )

    session_ids: list[str] = []

    def _load_sessions() -> list:
        with Session(engine) as db:
            sessions, _ = list_vehicle_sessions(
                db, tenant_id=tenant_id, status=None, active_only=False, page=1, per_page=50
            )
            return sessions

    # Warmup
    _load_sessions()
    with Session(engine) as db:
        sessions = _load_sessions()
        build_session_list_items(db, sessions=sessions)
        if sessions:
            build_session_console_context(db, tenant_id=tenant_id, session_id=sessions[0].id)
            build_route_context(db, tenant_id=tenant_id, session_id=sessions[0].id)
    session_ids = [s.id for s in sessions]

    results: dict[str, dict[str, float]] = {}

    def list_bench() -> object:
        with Session(engine) as db:
            sessions, _ = list_vehicle_sessions(
                db, tenant_id=tenant_id, status=None, active_only=False, page=1, per_page=50
            )
            return build_session_list_items(db, sessions=sessions)

    results["vehicle-sessions list"] = _measure(counter, list_bench, iterations=iterations)

    if session_ids:
        def console_bench() -> object:
            with Session(engine) as db:
                return build_session_console_context(
                    db, tenant_id=tenant_id, session_id=session_ids[0]
                )

        results["console-context"] = _measure(counter, console_bench, iterations=iterations)

        def route_bench() -> object:
            with Session(engine) as db:
                return build_route_context(db, tenant_id=tenant_id, session_id=session_ids[0])

        results["route-context"] = _measure(counter, route_bench, iterations=iterations)

    print(f"\nBenchmark logistics (dev DB, {len(session_ids)} sesiones, {iterations} iteraciones)")
    print("-" * 58)
    print(f"{'operacion':<24} {'min(ms)':>10} {'avg(ms)':>10} {'queries':>8}")
    print("-" * 58)
    for name, metrics in results.items():
        print(
            f"{name:<24} {metrics['min_ms']:>10.2f} {metrics['avg_ms']:>10.2f} "
            f"{metrics['queries']:>8.0f}"
        )
    print("-" * 58)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark endpoints logistics")
    parser.add_argument("--iterations", type=int, default=10, help="Iteraciones por operacion")
    args = parser.parse_args()
    run_benchmarks(args.iterations)


if __name__ == "__main__":
    main()
