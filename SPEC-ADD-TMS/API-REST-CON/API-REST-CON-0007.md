# A.SPEC API-REST-CON-0007 — Despliegue y ejecución del API en Win10

## WHY
El API debe estar disponible para Systutor (Termux) a través de la red
Tailscale, de forma persistente y segura.

## WHAT
- Build de `ERP-SYSTUTOR.API` (VB.NET 3.5).
- Abrir firewall de Win10 en puerto `8080` restringido a la subnet Tailscale.
- Ejecutar el API como servicio/keep-alive (no depende de la app ERP abierta).

## SCOPE
- Configuración de firewall en Win10.
- Registro del exe como servicio o tarea de inicio.
- `app.config` con el connection string al legacy (mismo que ERP).

## OUT OF SCOPE
- Lógica del API (A.SPEC 0001-0004).
- Consumidor Python (A.SPEC 0005-0006).

## CONTRACT
- El API es alcanzable desde Termux vía
  `http://<IP-Tailscale-Win10>:8080/api/health` → `200`.
- El puerto no está expuesto a Internet público (solo Tailscale).

## INVARIANTS
- No expone el puerto 8080 fuera de la subnet Tailscale.
- No altera la conectividad del ERP ni del SQL Server.

## VERIFICATION
- Desde Termux: `curl http://<IP-Tailscale-Win10>:8080/api/health` → `200`.
- `curl` sin token a `/api/clientes` → `401` (si 0004 aplicado).
- Reinicio de Win10 deja el API activo (servicio).

## ROLLBACK
- Cerrar puerto firewall y detener el servicio. Sin efecto en BD.

## CHANGE SURFACE
```yaml
allowed:
  - configuración firewall Win10
  - registro de servicio Win10
prohibited:
  - repositorio Systutor (esto es infra del entorno)
```

## BLAST RADIUS
```yaml
direct:
  - host Win10 (puerto 8080)
indirect:
  - todos los consumidores Systutor
must_not_affect:
  - SQL Server
  - ERP app
  - red pública
```
