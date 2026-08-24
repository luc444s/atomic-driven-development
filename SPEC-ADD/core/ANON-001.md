# A.SPEC ANON-001 — Anonimizar datos personales del sistema (nombres demo)

## WHY

La base de datos contiene nombres reales de personas y empresas (dueño,
proveedores, clientes, conductores), placas reales de vehículos, DNIs/RUCs y
correos personales. Cualquier demostración, captura o publicación expone esa
información. Se reemplazan por nombres genéricos demo que no corresponden a
entidades reales identificables.

## WHAT

Una transición observable: **ninguna consulta al sistema muestra nombres,
documentos, placas ni correos reales** — todo es datos demo claramente
genéricos. Mapeo:

| Entidad | Antes | Después |
|---|---|---|
| Proveedor | SIHUEN LUCAS ARMAS LESCANO | PROVEEDOR DEMO UNO S.A.C. |
| Cliente empresa | INVERSIONES VILLALFA S.A.C. | CLIENTE DEMO DOS S.A.C. |
| Cliente empresa | JAELIN E.I.R.L. | CLIENTE DEMO TRES E.I.R.L. |
| Cliente persona | CASTILLO QUISPE HECTOR ANIBAL | PEREZ PEREZ JUAN DEMO |
| Almacén central | OXIPUR EMPRESA INDIVIDUAL DE RESP. LIMITADA | ALMACEN CENTRAL DEMO |
| Almacén móvil | Movil RAM/BEI-793 | ALMACEN MOVIL VEH-001 |
| Vehículos | TAF-948 / T3G081 / RAM/BEI-793 | VEH-001 / VEH-002 / VEH-003 |
| Usuario dueño | sihuen8@gmail.com (nombre real) | dueno.demo@systutor.test · USUARIO DEMO SYSTUTOR |
| Conductores ×3 | nombres reales + @oxipur.com | CONDUCTOR DEMO UNO/DOS/TRES · conductor.N@systutor.test |
| Documentos | DNIs/RUCs reales | series 2XXXXXX000 / 4XXXXXXX0 ficticias |

Dominio `systutor.test` usa el TLD reservado `.test` — imposible que exista.
`SYSTUTOR` como marca comercial se conserva.

## SCOPE

- UPDATE sobre: com_suppliers (+contacts/documentos), crm_customers,
  lg_warehouses, lg_vehicles, users (email/full_name).
- Backup previo de las tablas afectadas.

## OUT OF SCOPE

- Direcciones físicas (calles reales en crm_customer_addresses) — fase 2 si el
  usuario lo pide.
- Seriales de cilindros (ya son TEST-*).
- Nombre del tenant ("Demo Tenant", ya genérico).
- Contraseñas.

## CONTRACT

Postcondiciones:

- `SELECT` sobre los campos de nombre/email/placa de las tablas afectadas no
  devuelve ningún string real actual.
- El usuario dueño inicia sesión con `dueno.demo@systutor.test` (contraseña
  sin cambios).
- Los IDs NO cambian: relaciones intactas.

## INVARIANTS

```yaml
invariants:
  - Ningún id cambia; solo campos descriptivos.
  - Los roles y permisos asignados persisten (se renombran, no se recrean).
  - La app sigue operativa: login, órdenes, despachos, jornadas.
```

## VERIFICATION

- Re-ejecutar el inventario de nombres → cero coincidencias con los valores
  anteriores (lista literal en este documento).
- Login con dueno.demo@systutor.test funciona y ve sus módulos con permisos.

## ROLLBACK

Restaurar desde `backups/anon_pre_backup_*.sql`. Sin efectos irreversibles más
allá del propio dato (los nombres viejos quedan solo en el backup local).

## Change Surface

```yaml
change_surface:
  allowed:
    - DB rows (UPDATE): com_suppliers, com_supplier_contacts, crm_customers,
      lg_warehouses, lg_vehicles, users
    - backups/
  prohibited:
    - cualquier DROP/ALTER de esquema
    - código fuente
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - datos maestros de demostración
  indirect:
    - snapshots de nombre (customer_name_snapshot) históricos — se dejan
      (registro histórico §45)
  must_not_affect:
    - ids, relaciones, permisos, stock, jornadas
```

## Composition

```yaml
composition:
  requires_aspecs: []
  systemic_invariants:
    - "Ninguna entidad demo colisiona con una empresa/persona real buscable."
```

## Traceability

- Requirement: pedido directo del usuario — nombres genéricos inexistentes.
- Estado: DONE tras ejecución + verificación.

## Definition of Done

- [x] Todas las anteriores (ejecutado inline; ver commits)
