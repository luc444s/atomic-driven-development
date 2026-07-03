# ECilindroEstadoActual — Uso y Cardinalidad

## DDL real (desde SPs)

```sql
CREATE TABLE dbo.ECilindroEstadoActual (
    Serie       VARCHAR(50),    -- Nro_Producto del cilindro (CodBarra)
    ProductoId  INT,            -- FK logica a Producto.Cod_Producto
    Estado      VARCHAR(30),    -- LLENO_EN_ALMACEN, VACIO_EN_ALMACEN, EN_RUTA, etc.
    Fecha       DATETIME,
    UsuarioId   INT,            -- FK logica a Persona_Nuevo
    AlmacenId   INT,            -- FK logica a Almacen
    Origen      VARCHAR(100)    -- 'Cambio de estado' por defecto
);
```

## ¿Siempre apunta al producto "envase" o a veces al gas?

**Siempre al envase.** `ProductoId` apunta al `Producto.Cod_Producto` que representa el cilindro físico (tipo de envase: "Bombona 15KG", "Bombona 45KG", etc.). El **gas** tiene su propio `Cod_Producto` distinto, y nunca se registra en `ECilindroEstadoActual`.

## Cardinalidad real

| Relación | Tipo | Evidencia |
|---|---|---|
| 1 cilindro (serie) → 1 ProductoId | Fija | `Serie` = `Producto.Nro_Producto`, `ProductoId` = `Producto.Cod_Producto` |
| 1 ProductoId → N cilindros | 1:N | Un tipo de envase ("Bombona 15KG") tiene muchas series |
| 1 ProductoId → 1 estado por serie | 1:1 | Cada serie tiene exactamente 1 registro en ECilindroEstadoActual |
| ProductoId + Serie | **PK lógica** | `WHERE ProductoId = @P AND Serie = @S` en `usp_Cilindro_CambiarEstado` |

## ¿Cambia con el tiempo o queda fijo por cilindro?

**El ProductoId queda fijo.** Una vez creado, el cilindro mantiene el mismo `ProductoId` (tipo de envase) de por vida. Lo que cambia es:
- `Estado` — transiciones: CREADO → LLENO_EN_ALMACEN → EN_RUTA → VACIO_EN_ALMACEN → ...
- `AlmacenId` — cuando se traslada
- `Fecha` — cada vez que se actualiza
- `Origen` — motivo del cambio

## Registro histórico: ECilindroEstadoLog

```sql
CREATE TABLE dbo.ECilindroEstadoLog (
    Serie        NVARCHAR(100),
    Estado       NVARCHAR(50),
    Fecha        DATETIME,
    Usuario      INT,
    Observacion  NVARCHAR(300),
    Origen       NVARCHAR(100),
    MotivoCodigo VARCHAR(30),
    AlmacenId    INT
);
```

Cada transición de estado se registra en el log. SPs disponibles:
- `usp_Cilindro_Estado_LogSingle` — un cilindro
- `usp_Cilindro_Estado_LogBulk` — múltiples vía TVP
- `usp_Cilindro_InsertarEstado` — con validación TRY/CATCH
- `usp_Cilindro_RegistrarCreacion` — estado inicial "CREADO"

## Validación de transiciones

`ECilindroEstadoTransicion` define qué transiciones están permitidas:

```
EstadoOrigen → EstadoDestino (ej: LLENO_EN_ALMACEN → EN_RUTA)
```

`usp_Cilindro_CambiarEstado` valida contra esta tabla antes de actualizar.
