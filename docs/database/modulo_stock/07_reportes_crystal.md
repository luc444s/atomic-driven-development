# Reportes Crystal del Módulo Stock/Inventario

---

## Reportes identificados

| Reporte | Form de origen | Propósito | Tabla temporal usada |
|---------|---------------|-----------|---------------------|
| CRalmacengen | FrmMostrarSotckGeneral | Stock general con costos | Reporte (crearreporte) |
| CRalmacengen1 | FrmMostrarSotckRaz | Stock por razón social | Reporte |
| CRalmacengen2 | FrmMostrarSotckxMarca | Stock por marca | Reporte |
| CRalmacengen3 | FrmMostrarSotckxpROV | Stock por proveedor | Reporte |
| CRalmacengen4 | FrmMostrarSotck / FrmMostrarSotckMCERO | Stock por almacén | Reporte |
| CRstockCySMilton | No identificado | Stock por almacén (vista) | Vista CRstockCySMilton |

---

## Flujo de reportes

1. El form llama a `objM.Eliminarreporte()` — limpia la tabla temporal `Reporte`
2. Itera sobre el ListView — para cada fila llama a `objM.crearreporte()` que inserta un registro en la tabla temporal
3. Crea instancia del reporte Crystal
4. Configura conexión con credenciales de BD desde `app.config`
5. Asigna el reporte al visor

### Peligro de seguridad

Las credenciales de BD se pasan en **texto plano** desde `ConfigurationManager.AppSettings`:
```vb.net
.ServerName = ConfigurationManager.AppSettings.Get("servername").ToString
.UserID = "sa"
.Password = ConfigurationManager.AppSettings.Get("password").ToString
```

Esto expone la contraseña de SA en el archivo de configuración y en memoria.

---

## Tabla temporal "Reporte"

Los reportes usan una tabla llamada `Reporte` (o similar) que se llena mediante el método `crearreporte()` y se limpia con `Eliminarreporte()`. Esta tabla no tiene FK y podría acumular datos residuales si no se limpia correctamente.

**Riesgo:** Si el form se cierra antes de completar el reporte, la tabla temporal queda con datos huérfanos.

---

## Búsqueda de archivos .rpt

```bash
Get-ChildItem -Recurse -Filter "*.rpt" | Where-Object { $_.Name -like "*almacen*" -or $_.Name -like "*stock*" -or $_.Name -like "*inventario*" }
```

No se encontraron archivos .rpt específicos de stock en el proyecto. Los reportes deben estar compilados como recursos embebidos (CRalmacengen, CRalmacengen1, etc. son clases compiladas).
