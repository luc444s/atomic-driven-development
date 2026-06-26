# Decisión: Arquitectura Limpia para Nuevos Módulos

**Fecha:** 26/06/2026
**Contexto:** Decisión sobre cómo construir los nuevos módulos de trazabilidad de cilindros.

---

## 1. Decisión

A partir de este hito, **los módulos nuevos** de trazabilidad de cilindros se construyen con:

- **No usar stored procedures nuevos** para lógica de negocio
- **Toda la lógica en VB.NET** (capa de aplicación + dominio)
- **Dapper** como micro-ORM para acceso a datos
- **Arquitectura limpia en 3 capas** dentro del mismo proyecto (`ERP-SYSTUTOR.vbproj`)
- **Las tablas SQL existentes se reutilizan** sin migración

## 2. Justificación

1. El proyecto ya está en .NET Framework 4.7.2, que soporta interfaces, genéricos, LINQ, async/await
2. Los 944 SPs existentes no se modifican — el legacy sigue funcionando igual
3. Dapper es liviano y no requiere cambios mayores en el proyecto
4. La lógica de trazabilidad es suficientemente acotada como para aislarla del monolito
5. Un mes es plazo insuficiente para migrar a Python/FastAPI/PostgreSQL desde cero

## 3. Evaluación de Alternativas

| Opción | ¿Cumple el plazo (1 mes)? | ¿Deja base mantenible? | Veredicto |
|---|---|---|---|
| Reparar legacy como está (solo bugs) | Sí | No | ❌ |
| Python + FastAPI + PostgreSQL desde cero | No | Sí | ❌ |
| Híbrido: capa nueva VB.NET + legacy corregido | Sí | Sí | ✅ |

### Por qué NO conviene Python en 1 mes

1. El modelo de datos de cilindros ya existe en SQL Server con 184 tablas. Migrar a PostgreSQL implica rediseñar todo el esquema, migrar datos históricos y validar constraints. Eso son 2-3 semanas.
2. La lógica de negocio de cilindros está en ~75 SPs que manejan casos borde reales: cambios de dueño, prueba hidráulica, estados de cilindro, carga peligrosa. En 1 mes no se reescribe todo testeando bordes.
3. FastAPI es backend solamente. El frontend requeriría otra tecnología (React/Vue) agregando otro mes.
4. El alcance (6-7 módulos de trazabilidad) es demasiado grande para 1 mes desde cero.

## 4. Consecuencias

**Positivas:**
- Los módulos nuevos serán mantenibles, testeables y sin SPs
- El legacy no se rompe — se toca lo mínimo indispensable
- Se crea una base reusable para futuros módulos
- El equipo aprende Clean Architecture gradualmente

**Negativas:**
- El sistema será híbrido (SPs + Dapper) durante años
- Se requiere disciplina para no mezclar estilos
- Las transacciones que crucen SPs y código nuevo requerirán `TransactionScope`

## 5. Lo que NO se hace en esta iteración

- No se toca `CAtencion.vbproj` (sigue en .NET 4.0)
- No se refactoriza `Cgas.vb`
- No se modifican SPs existentes
- No se tocan Crystal Reports existentes
- No se migra a Python ni a PostgreSQL
- No se reescriben forms legacy que funcionan

## 6. Arquitectura Propuesta

### Estructura de carpetas (dentro de ERP-SYSTUTOR.vbproj)

```
ERP-SYSTUTOR/
├── Trazabilidad/
│   ├── Domain/
│   │   ├── Entities/
│   │   │   ├── Cilindro.vb
│   │   │   ├── Cliente.vb
│   │   │   ├── PuntoEntrega.vb
│   │   │   ├── MovimientoCilindro.vb
│   │   │   ├── AgendaRepartidor.vb
│   │   │   └── EstadoCilindro.vb
│   │   └── Enums/
│   │       └── EstadoCilindroEnum.vb
│   │
│   ├── Application/
│   │   ├── Interfaces/
│   │   │   ├── ICilindroRepository.vb
│   │   │   ├── IAgendaRepository.vb
│   │   │   ├── IMovimientoRepository.vb
│   │   │   └── IClienteRepository.vb
│   │   ├── UseCases/
│   │   │   ├── RegistrarSalidaCilindro.vb
│   │   │   ├── RegistrarIngresoCilindro.vb
│   │   │   ├── PlanificarRuta.vb
│   │   │   ├── PrepararCarga.vb
│   │   │   ├── ConfirmarTraslado.vb
│   │   │   └── ConsultarHistorialCilindro.vb
│   │   └── DTOs/
│   │       ├── SalidaCilindroDto.vb
│   │       ├── PlanificacionDiariaDto.vb
│   │       └── HistorialCilindroDto.vb
│   │
│   └── Infrastructure/
│       ├── Data/
│       │   ├── DbContext.vb
│       │   ├── Repositories/
│       │   │   ├── CilindroRepository.vb  (Dapper)
│       │   │   ├── AgendaRepository.vb    (Dapper)
│       │   │   ├── MovimientoRepository.vb (Dapper)
│       │   │   └── ClienteRepository.vb   (Dapper)
│       │   └── Mappings/
│       │       └── EntityMappings.vb
│       └── Services/
│           ├── AgendaService.vb
│           └── TrazabilidadService.vb
│
└── Forms/
    └── Trazabilidad/
        ├── FrmPlanificacionDiaria.vb
        ├── FrmSalidaConAgenda.vb
        ├── FrmCargaCamion.vb
        └── FrmHistorialCilindro.vb
```

### Capas y responsabilidades

| Capa | Responsabilidad | Tecnología |
|---|---|---|
| **Domain** | Entidades puras, value objects, enums, reglas de negocio sin dependencias externas | VB.NET puro |
| **Application** | Use cases, DTOs, interfaces de repositorio, orquestación | VB.NET + interfaces |
| **Infrastructure** | Repositorios (Dapper), servicios de infraestructura | Dapper + ADO.NET |
| **Presentation** | Forms WinForms que delegan en Application layer | WinForms |

### Flujo de datos

```
Form (UI)
  │ Llama a Use Case (constructor injection)
  ▼
Application / UseCase
  │ Usa interfaces de repositorio
  ▼
Infrastructure / Repository (Dapper)
  │ Ejecuta SQL parametrizado contra SQL Server
  ▼
SQL Server (tablas existentes)
```

### Principios

- **Inyección de dependencias manual** — no hay DI container nativo; se usa constructor injection con factories
- **Dapper para todo acceso a datos nuevo** — nada de SPs nuevos
- **Transacciones con `TransactionScope`** cuando un use case abarca múltiples operaciones
- **Los SPs existentes no se tocan** — se usan solo desde forms legacy

## 7. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Mezclar estilos (SP + Clean) causa confusión | Medio | El equipo debe entender que los SPs existentes NO se tocan |
| Transacciones que cruzan SPs y código nuevo | Alto | Usar `TransactionScope` |
| Rendimiento: Dapper vs SP en consultas pesadas | Bajo | Dapper es casi tan rápido como ADO.NET puro |
| Acoplamiento con forms legacy | Medio | Forms nuevos se inyectan vía el mismo mecanismo de menú |
| El equipo no conoce Clean Architecture | Medio | La estructura es simple, no se necesita un framework complejo |
| Crystal Reports requiere SPs | Bajo | Reportes legacy siguen usando SPs; reportes nuevos usan DataTables |
