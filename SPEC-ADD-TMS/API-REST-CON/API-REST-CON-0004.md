# A.SPEC API-REST-CON-0004 — Autenticación del API legacy

## WHY
El API queda expuesto en la red Tailscale; debe autenticarse para que solo
Systutor (u otros módulos autorizados) lo consuman.

## WHAT
Validación de cabecera `Authorization: Bearer <token>` en todas las rutas de
datos. `GET /api/health` queda público.

## SCOPE
- Middleware/filtro de auth en el listener de `ERP-SYSTUTOR.API`.
- Verificación de token firmado o lista de tokens válidos.

## OUT OF SCOPE
- Emisión y rotación de tokens (depende de **D3**).
- Autenticación de usuarios finales.

## CONTRACT
- Sin token válido → `401 Unauthorized`.
- Con token válido → la ruta continúa normalmente.
- El token identifica al consumidor Systutor (no al usuario final legacy).

## INVARIANTS
- No debilita la ley de frontera: TMS sigue sin tocar SQL Server.
- No expone credenciales de SQL Server en el API.

## VERIFICATION
- Con token válido → `200` en `/api/clientes`.
- Sin token → `401`.
- Token inválido → `401`.

## ROLLBACK
- Deshabilitar el filtro de auth (volver a 0002 sin auth, solo para debug
  controlado). Compensación: cerrar puerto firewall.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
  - ERP-SYSTUTOR.API/Security/*.vb
prohibited:
  - plugins/**
```

## BLAST RADIUS
```yaml
direct:
  - todas las rutas del API
indirect:
  - consumidores Systutor
must_not_affect:
  - datos legacy
  - ERP app
```

> **Pendiente D3**: definir mecanismo (token estático compartido systutor,
> JWT, o usuario de servicio). Esta A.SPEC queda sujeta a D3.
