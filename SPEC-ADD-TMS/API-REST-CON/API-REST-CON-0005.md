# A.SPEC API-REST-CON-0005 — Cliente tipado Python (anti-corruption adapter)

## WHY
TMS/crm debe consumir el API legacy sin acoplar su código al esquema VB.
Se aísla la frontera en un adaptador tipado (patrón `api-rest-connector`).

## WHAT
Módulo cliente HTTP en Systutor que consume `ERP-SYSTUTOR.API`:
- `get_clientes() -> list[ClienteLegacy]`
- `get_puntos(cliente_id) -> list[PuntoLegacy]`
Tipado, con query keys y manejo de scope/errores.

## SCOPE
- Cliente HTTP (httpx) con timeout, reintentos y parseo a dataclasses Pydantic.
- Configuración de base URL y token vía settings (no hardcode).

## OUT OF SCOPE
- Mapeo a `crm.Customer` (A.SPEC 0006).
- Lógica de negocio de clientes.

## CONTRACT
- Función async que retorna tipos locales (`ClienteLegacy`).
- URLs y token configurables por entorno.
- No muestra IDs crudos al usuario; resuelve etiquetas en capa superior.
- Falla explícitamente ante `401`/`timeout`/JSON inválido.

## INVARIANTS
- Nunca lee SQL Server legacy; solo HTTP al API.
- No importa páginas internas de otros plugins.

## VERIFICATION
- Test happy path con mock del API → lista tipada correcta.
- Test `401` → excepción controlada.
- Test respuesta vacía → lista vacía, sin error.
- Test `Timeout` → reintento/error controlado.

## ROLLBACK
- Eliminar el módulo adaptador. Sin efecto en BD.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/<crm|tms>/backend/legacy/clientes.py   # según D4
  - plugins/<crm|tms>/backend/legacy/schemas.py
prohibited:
  - kernel/**
  - plugins/logistics/**
```

## BLAST RADIUS
```yaml
direct:
  - módulo adaptador en Systutor
indirect:
  - crm.Customer (vía 0006)
must_not_affect:
  - SQL Server legacy
  - ERP app
```

> **Pendiente D4**: decidir si el adaptador vive en `plugins/crm` o en un nuevo
> `plugins/tms`. El change surface se fija según D4.
