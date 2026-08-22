from __future__ import annotations

import re

from plugins.tms.backend import ports

_DRIVER_ROLE_NAME = "driver"
_DRIVER_DOMAIN = "@oxipur.com"
_DNI_DIRTY_PREFIX = re.compile(r"^D(\d{8}?)\s*-", re.IGNORECASE)
_DNI_INLINE = re.compile(r"\bD(\d{8})\b", re.IGNORECASE)


def driver_email(dni: str) -> str:
    return f"{dni}{_DRIVER_DOMAIN}"


def normalize_driver_dni(dnichofer: str, transportista: str = "") -> str:
    """Resuelve el DNI real del chofer. El legacy guarda nombres sucios:
    'D44973574-HIRVING...' en Transportista y dnichofer inconsistente (4492/10725/1164).
    Prioridad: prefijo 'D<8dígitos>' del nombre; fallback dnichofer si tiene 8 dígitos.
    """
    if transportista:
        m = _DNI_DIRTY_PREFIX.search(transportista.strip())
        if m:
            return m.group(1)
        m = _DNI_INLINE.search(transportista.strip())
        if m:
            return m.group(1)
    clean = (dnichofer or "").strip()
    if re.fullmatch(r"\d{8}", clean):
        return clean
    return ""


def ensure_driver_user(
    db,
    *,
    tenant_id: str,
    branch_id: str | None,
    dni: str,
    full_name: str,
) -> str:
    """Garantiza el User conductor vía puerto; devuelve su id."""
    dni = dni.strip()
    return ports.get_ports().ensure_driver(
        db,
        tenant_id=tenant_id,
        branch_id=branch_id,
        dni=dni,
        full_name=full_name.strip() or f"Conductor {dni}",
    )


__all__ = ["driver_email", "ensure_driver_user", "normalize_driver_dni"]
