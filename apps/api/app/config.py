from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from systutor.core.config import (
    Settings,
    env_settings_kwargs,
    load_env_file,
    register_settings_factory,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


class GasSettings(Settings):
    use_transactional_stock_bridge: bool = True
    allow_legacy_stock_fallback: bool = False
    allow_cylinder_product_fallback: bool = True
    allow_seed_orphan_repair_fallback: bool = False
    logistics_routing_enabled: bool = False
    logistics_osrm_base_url: str | None = None
    logistics_vroom_base_url: str | None = None
    logistics_routing_request_timeout_seconds: int = 10
    logistics_routing_cache_ttl_seconds: int = 300
    logistics_waybill_issuer_legal_name: str | None = None
    logistics_waybill_issuer_address_line: str | None = None
    logistics_waybill_issuer_postal_city_line: str | None = None
    plugins_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "plugins")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> GasSettings:
    load_env_file(DEFAULT_ENV_FILE)
    kwargs = env_settings_kwargs(env_file=None)
    kwargs["plugins_dir"] = Path(
        os.getenv("SYSTUTOR_PLUGINS_DIR", str(PROJECT_ROOT / "plugins"))
    )
    return GasSettings(
        **kwargs,
        use_transactional_stock_bridge=_env_bool("SYSTUTOR_USE_TRANSACTIONAL_STOCK_BRIDGE", True),
        allow_legacy_stock_fallback=_env_bool("SYSTUTOR_ALLOW_LEGACY_STOCK_FALLBACK", False),
        allow_cylinder_product_fallback=_env_bool(
            "SYSTUTOR_ALLOW_CYLINDER_PRODUCT_FALLBACK", True
        ),
        allow_seed_orphan_repair_fallback=_env_bool(
            "SYSTUTOR_ALLOW_SEED_ORPHAN_REPAIR_FALLBACK", False
        ),
        logistics_routing_enabled=_env_bool("SYSTUTOR_LOGISTICS_ROUTING_ENABLED", False),
        logistics_osrm_base_url=os.getenv("SYSTUTOR_LOGISTICS_OSRM_BASE_URL") or None,
        logistics_vroom_base_url=os.getenv("SYSTUTOR_LOGISTICS_VROOM_BASE_URL") or None,
        logistics_routing_request_timeout_seconds=int(
            os.getenv("SYSTUTOR_LOGISTICS_ROUTING_REQUEST_TIMEOUT_SECONDS", "10")
        ),
        logistics_routing_cache_ttl_seconds=int(
            os.getenv("SYSTUTOR_LOGISTICS_ROUTING_CACHE_TTL_SECONDS", "300")
        ),
        logistics_waybill_issuer_legal_name=os.getenv(
            "SYSTUTOR_LOGISTICS_WAYBILL_ISSUER_LEGAL_NAME"
        )
        or None,
        logistics_waybill_issuer_address_line=os.getenv(
            "SYSTUTOR_LOGISTICS_WAYBILL_ISSUER_ADDRESS_LINE"
        )
        or None,
        logistics_waybill_issuer_postal_city_line=os.getenv(
            "SYSTUTOR_LOGISTICS_WAYBILL_ISSUER_POSTAL_CITY_LINE"
        )
        or None,
    )


register_settings_factory(get_settings)
