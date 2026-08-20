# TMS — Transport Management System

Integracion con el legacy ERP-SYSTUTOR (VB.NET) via `ERP-SYSTUTOR.API` (HTTP, Win10).

Ley de frontera: Python NUNCA toca SQL Server legacy; solo consume el API REST.
Legacy es fuente de verdad de lectura (clientes, productos, stock, almacenes).
Unico write-back permitido: `POST /api/stock/movement` (egreso idempotente, ADR D5).

## Estructura

- `backend/legacy/client.py` — cliente HTTP tipado (anti-corruption adapter)
- `backend/legacy/schemas.py` — modelos Pydantic de los contratos legacy
- `backend/services/link_legacy.py` — enlaces legacy -> OSS (crm, productos, stock, logistics)
- `backend/commands/link_legacy.py` — runner CLI de sincronizacion

## Uso

```bash
# sincronizar todo (clientes, productos, almacenes — NO stock)
.venv/bin/python -m plugins.tms.backend.commands.link_legacy --all

# por dominio
.venv/bin/python -m plugins.tms.backend.commands.link_legacy --clientes --productos --almacenes
```

Stock NO se sincroniza: legacy es dueño del stock (computado). OSS solo hace
write-back de egresos (salida a cliente) via `POST /api/stock/movement`. Si un
flujo necesita leer stock puntual, usar `client.get_stock()` (read-through).

## Configuracion (.env)

- `SYSTUTOR_LEGACY_API_BASE_URL` — ej. `http://100.68.121.21:8080/api`
- `SYSTUTOR_LEGACY_API_TOKEN` — Bearer token compartido del API legacy

## Specs

Ver `SPEC-ADD-TMS/API-REST-CON/` (A.SPEC 0005, 0006, 0010, 0012, 0014, 0015, 0016).
