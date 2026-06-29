# Clases VB Adicionales — Módulo Logística

## ModPlanificacionUtils.vb

| Atributo | Valor |
|---|---|
| **Ruta** | Módulo VB en proyecto de planificación |
| **Propósito** | Utilidades compartidas para los formularios de planificación |
| **Métodos principales** | `ProcesarTooltipParcial()` — Muestra tooltip informativo cuando un pedido tiene estado PARCIAL (stock insuficiente). Colorea el control según estado (verde/amarillo/rojo). |
| **Forms que lo usan** | `PlanificacionADR.vb`, `FrmPlanificacion (Antiguo).vb`, `ZZZFrmRegPlanificacionPro.vb` |
| **Riesgo** | Lógica duplicada parcialmente entre forms. Posibles discrepancias de color si se modifica en un solo lugar. |

---

## ModFacturacion_Despacho.vb

| Atributo | Valor |
|---|---|
| **Ruta** | Módulo VB de facturación |
| **Propósito** | Lógica compartida de despacho entre facturación y logística |
| **Funcionalidad** | Actualización de cantidades despachadas, cierre de despacho, generación de guías. |
| **SPs que usa** | `actualizar_despacho`, `cerrar_despacho`, `Movimiento_guia` |
| **Forms que lo usan** | `FrmDespacho.vb` |
| **Riesgo** | Módulo compartido entre dos áreas (facturación y logística). Cambios en lógica de despacho afectan ambos módulos. |

---

## ReporteCartaPorteUI.vb

| Atributo | Valor |
|---|---|
| **Ruta** | UI de reportes / logística |
| **Propósito** | Interfaz de usuario para generación de reportes Carta Porte |
| **Funcionalidad** | Selección de movimiento, filtros, previsualización y exportación de carta porte. |
| **SPs que usa** | `usp_CartaPorte_Cabecera`, `usp_CartaPorte_Detalle`, `usp_CartaPorte_Resumen` |
| **Vistas que usa** | `vCartaPorte` |
| **Riesgo** | Contiene lógica de presentación y negocio mezcladas. Datos ADR visibles. |

---

## GeocodingProvider.vb

| Atributo | Valor |
|---|---|
| **Ruta** | Módulo de geocodificación |
| **Propósito** | Proveedor de geocodificación para convertir direcciones en coordenadas GPS |
| **Estado** | **No implementado** — Stub/Mock. Siempre retorna `(0, 0)`. |
| **Métodos** | `GetCoordinates(address As String) As GeoResult` |
| **Riesgo** | Código sin implementación real. Coordenadas inválidas en reportes de ruta. Falsa sensación de funcionalidad. |

---

## GeoResult.vb

| Atributo | Valor |
|---|---|
| **Ruta** | Módulo de geocodificación |
| **Propósito** | Modelo de resultado de geocodificación |
| **Propiedades** | `Latitude As Double`, `Longitude As Double`, `Success As Boolean`, `ErrorMessage As String` |
| **Uso** | Clase de retorno para `GeocodingProvider.GetCoordinates()` |
| **Riesgo** | Bajo. Solo modelo de datos. |

---

## ResultadoEntrega.vb

| Atributo | Valor |
|---|---|
| **Ruta** | Módulo de logística / agenda |
| **Propósito** | Modelo de resultado de entrega (usado en Módulo Recojo para cierre de tareas) |
| **Propiedades** | `IdAgenda`, `Serie`, `EstadoFinal`, `Observacion`, `Foto`, `Firma`, `CoordenadaFin` |
| **Uso** | Procesamiento de resultados de entrega desde el Módulo Recojo. |
| **Riesgo** | Contiene datos sensibles (foto, firma, coordenada). La firma y foto pueden tener implicaciones legales. |
