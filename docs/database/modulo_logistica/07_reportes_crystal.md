# Reportes Crystal del Módulo Logística

## CR_AgendaRutaDia

| Atributo | Valor |
|---|---|
| **Formulario que lo invoca** | `FrmAgendaRepartidor` — botón "Reporte Ruta" |
| **SP / Vista que usa** | Directo a `AGENDA_REPARTIDOR` con filtro por fecha y repartidor |
| **Credenciales** | `sa` / `password` (hardcodeadas en el archivo .rpt) |
| **Descripción** | Reporte de ruta diaria del repartidor. Muestra la secuencia de entregas programadas con dirección, cliente, producto y cantidad. |
| **Riesgo** | Acceso directo con credenciales SA. No usa SP parametrizado. |

---

## vTICKETGUIA1

| Atributo | Valor |
|---|---|
| **Formulario que lo invoca** | `FrmDespacho` — impresión de guía de despacho |
| **SP / Vista que usa** | Vista `vTICKETGUIA1` (en base de datos) |
| **Credenciales** | `sa` / `password` (hardcodeadas en el archivo .rpt) |
| **Descripción** | Ticket de guía de despacho con datos del movimiento, cliente, productos y cantidades. |
| **Riesgo** | Credenciales SA hardcodeadas. Vista directamente expuesta. |

---

## CRReporteProfalbaranCarga

| Atributo | Valor |
|---|---|
| **Formulario que lo invoca** | `FrmMovTrasladoAlmacen` |
| **SP / Vista que usa** | Posible vista o consulta directa a `Movimiento` + `DetalleMovimiento` |
| **Credenciales** | `sa` / `password` (hardcodeadas) |
| **Descripción** | Reporte de carga/traslado entre almacenes. Incluye detalle de productos y cantidades. |
| **Riesgo** | Credenciales SA. Datos de traslado expuestos. |

---

## Reportes Carta Porte

| Atributo | Valor |
|---|---|
| **Formulario que lo invoca** | `ReporteCartaPorteUI.vb` |
| **SP / Vista que usa** | `usp_CartaPorte_Cabecera`, `usp_CartaPorte_Detalle`, `usp_CartaPorte_Resumen`, `vCartaPorte` |
| **Credenciales** | Posiblemente `sa` / `password` |
| **Descripción** | Conjunto de reportes para documento Carta Porte (cabecera, detalle de productos, resumen ADR). |
| **Riesgo** | Datos sensibles de transporte y mercancías peligrosas. |

---

## ReporteCargaPeligrosa

| Atributo | Valor |
|---|---|
| **Formulario que lo invoca** | Módulo ADR / Carga Peligrosa |
| **SP / Vista que usa** | `usp_ADR_CalcularPuntosDocumento`, `vw_EdetPB_Vigente` |
| **Credenciales** | Posiblemente `sa` / `password` |
| **Descripción** | Reporte de carga peligrosa con detalle de puntos ADR, clases de peligro, túneles y cantidades. |
| **Riesgo** | Información crítica de seguridad. Credenciales SA si aplica. |

---

## Resumen de Riesgos Comunes

| Reporte | Credenciales SA | Sin SP | Datos Sensibles |
|---|---|---|---|
| CR_AgendaRutaDia | SI | SI | SI (rutas, contactos) |
| vTICKETGUIA1 | SI | SI | SI (clientes, productos) |
| CRReporteProfalbaranCarga | SI | SI | SI (traslados) |
| Reportes Carta Porte | Probable | NO | SI (ADR, transportistas) |
| ReporteCargaPeligrosa | Probable | NO | SI (ADR, seguridad) |
