# Datos Sensibles — Módulo Logística

## Identificación de Datos Sensibles

### Coordenadas GPS
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `Registro_Coordenadas.Latitud` | Latitud de repartidores y clientes | Geolocalización precisa de operaciones y clientes |
| `Registro_Coordenadas.Longitud` | Longitud de repartidores y clientes | Geolocalización precisa de operaciones y clientes |
| `AGENDA_REPARTIDOR.Latitud_Inicio` | Coordenada de inicio de ruta | Ubicación de repartidores |
| `AGENDA_REPARTIDOR.Longitud_Inicio` | Coordenada de inicio de ruta | Ubicación de repartidores |

**Nota:** Actualmente registra `(0, 0)` cuando no hay GPS real, pero el schema soporta datos reales.

### Direcciones de entrega
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `Vehiculo_cliente_nuevo.Direccion` | Dirección completa de punto de entrega | Domicilios de clientes |
| `Vehiculo_cliente_nuevo.Referencia` | Referencia de ubicación | Información adicional de ubicación |
| `Vehiculo_cliente_nuevo.Ubigeo` | Código de ubicación geográfica | Zona geográfica del cliente |

### Contactos y teléfonos
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `Vehiculo_cliente_nuevo.Contacto` | Nombre de contacto en punto de entrega | Datos personales |
| `Vehiculo_cliente_nuevo.Telefono` | Teléfono de contacto | Datos personales |
| `Cliente.Telefono` | Teléfono principal del cliente | Datos personales |
| `Cliente.Contacto` | Nombre de contacto | Datos personales |

### Credenciales de base de datos
| Ubicación | Credencial | Riesgo |
|---|---|---|
| Archivos `.rpt` (Crystal Reports) | Usuario: `sa` | **CRÍTICO** — Acceso total a la base de datos |
| Archivos `.rpt` (Crystal Reports) | Contraseña: `password` | **CRÍTICO** — Acceso total a la base de datos |

**Archivos afectados:**
- `CR_AgendaRutaDia.rpt`
- `vTICKETGUIA1.rpt`
- `CRReporteProfalbaranCarga.rpt`
- Posibles otros reportes .rpt

### Datos de transportistas y choferes
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `Transportista.Nombre` | Nombre del transportista | Datos de proveedores |
| `Transportista.RUC` | RUC del transportista | Datos fiscales |
| `Transportista.Placa` | Placa del vehículo | Datos del vehículo |
| `Chofer.Nombre` | Nombre del chofer | Datos personales |
| `Chofer.Licencia` | Número de licencia de conducir | Datos personales |

### Rutas y horarios de reparto
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `AGENDA_REPARTIDOR` | Tareas de reparto con fechas | Información operativa sensible |
| `AGENDA_REPARTIDOR.Hora_Inicio` | Hora de inicio de atención | Horarios de clientes |
| `AGENDA_REPARTIDOR.Hora_Fin` | Hora de fin de atención | Horarios de clientes |
| `RutaPto` | Puntos de ruta | Secuencia de entregas |

### Información ADR
| Tabla/Columna | Descripción | Riesgo |
|---|---|---|
| `EDetalle_PB.ClaseADR` | Clase de peligro ADR | Información de seguridad crítica |
| `EDetalle_PB.PuntosADR` | Puntos de peligro ADR | Información de seguridad crítica |
| `EDetalle_PB.Tunel` | Restricción de túnel | Información de seguridad crítica |

---

## Nivel de Sensibilidad

| Categoría | Nivel | Prioridad Migración |
|---|---|---|
| Credenciales SA en .rpt | **CRÍTICO** | Inmediata |
| Coordenadas GPS | ALTO | Alta |
| Direcciones y contactos | ALTO | Alta |
| Datos de transportistas | MEDIO | Media |
| Rutas y horarios | MEDIO | Media |
| Información ADR | MEDIO | Media |

---

## Recomendaciones

1. Eliminar credenciales `sa` de los archivos `.rpt` y usar autenticación integrada o usuario restringido.
2. Implementar enmascaramiento de coordenadas GPS en logs y reportes.
3. Revisar permisos de las tablas con datos sensibles (mínimo privilegio).
4. No exponer direcciones completas en reportes externos.
5. Encriptar datos personales (contactos, teléfonos) en la nueva arquitectura.
