# Módulo Clientes — Reportes Crystal

## 1. Reportes .rpt que filtran por cliente

| Reporte | Clase VB | Llamado desde | Parámetros | Filtro |
|---------|----------|--------------|------------|--------|
| `CRreporte_persona.rpt` | `Reportes\CRreporte_persona.vb` | FrmCatClientes, FrmRegClientePRO, FrmRegClientePLUS, FrmRegCliente, FrmCatProveedores | `codpersona` (int) | Cliente específico |
| `CRAlmacen_EnvasesXcliente.rpt` | `Reportes\CRAlmacen_EnvasesXcliente.vb` | MDIMenu ("NotificacionFormatoA4") | Ninguno | `ubicacion = 'CLIENTE'` |
| `CRAlmacen_EnvasesXclienteFormatoChico2.rpt` | `Reportes\CRAlmacen_EnvasesXclienteFormatoChico2.vb` | MDIMenu ("FormatoChico2") | Ninguno | Ninguno |
| `CRAlmacen_EnvasesVencen4a8cliente.rpt` | `Reportes\CRAlmacen_EnvasesVencen4a8cliente.vb` | MDIMenu | Ninguno | Interno del .rpt |
| `CRAlmacen_EnvasesVencen9amascliente.rpt` | `Reportes\CRAlmacen_EnvasesVencen9amascliente.vb` | MDIMenu | Ninguno | Interno del .rpt |
| `CRAlmacen_DevolucionesAtiempoXcliente.rpt` | `Reportes\CRAlmacen_DevolucionesAtiempoXcliente.vb` | MDIMenu | Ninguno | `ubicacion = 'CLIENTE' AND DIAS BETWEEN 32 AND 90` |
| `CRDeudasxCobrar.rpt` | `Reportes\CRDeudasxCobrar.vb` | FrmReportedxc | Ninguno | General (no filtra) |
| `CREstadoCtaAdm.rpt` | `Reportes\CREstadoCtaAdm.vb` | FrmCajaAdministrativaRep | `@movimiento`, `@DESCRIPCION` | Por tipo movimiento |
| `vTICKETFAC.rpt` | `Reportes\vTICKETFAC.vb` | Frmmovimientos | `codigo` (int) | Factura específica |
| `vTICKETFACPRO.rpt` | `Reportes\vTICKETFACPRO.vb` | Facturación PRO | `codigo` + subreporte cliente | Factura específica |
| `vTICKETFACcr.rpt` | `Reportes\vTICKETFACcr.vb` | FrmMovFacturacion | `codigo` | Factura específica |

## 2. Reportes NO usados (posible código muerto)

| Reporte | Estado |
|---------|--------|
| `CRDeudasxCobrarBACK.rpt` | Clase existe, no referenciada |
| `CRLetras.rpt` | Clase existe, no referenciada |
| `CRFacturacion.rpt` | Clase existe, no referenciada |
| `CRFacturacion1.rpt` | Clase existe, no referenciada |
| `vTICKETFACcliente.rpt` | Solo usado como subreporte de vTICKETFACPRO |

## 3. Patrones de carga

### Patrón 1 — Clase wrapper + conexión manual (legacy)
```vb.net
Dim obj2 As New CRreporte_persona
For Each tb In obj2.Database.Tables
    ' configurar ServerName/UserID/Password/DatabaseName desde AppSettings
Next
obj2.SetParameterValue("codpersona", codigoCliente)
CrystalReportViewer1.ReportSource = obj2
```

### Patrón 2 — AplicarConexionReporte + MostrarReporte
```vb.net
Dim objM As New CRAlmacen_EnvasesXcliente
AplicarConexionReporte(objM)
Dim f As New FrmReportes
f.FormulaSeleccion = "{Valmacen_envases.ubicacion} = ""CLIENTE"""
f.MostrarReporte(objM)
f.Show()
```

## 4. Vistas de BD usadas por reportes

| Vista | Reporte asociado |
|-------|-----------------|
| `Vreporte_persona` | CRreporte_persona |
| `VESTADO_CUENTA_ADM` | CREstadoCtaAdm |
| `Valmacen_envases` | CRAlmacen_EnvasesXcliente, CRAlmacen_EnvasesVencen*, CRAlmacen_DevolucionesAtiempoXcliente |
| `VTICKET` | vTICKETFAC, vTICKETFACPRO, vTICKETFACcr |
| `VTicketDatosCLI` | vTICKETFAC (datos del cliente) |
| `VlistarVentasImpagas` | CRDeudasxCobrar |
| `Vimpresion_letra` | CRLetras |

## 5. Riesgos

- **CRDeudasxCobrarBACK**, **CRLetras**, **CRFacturacion**, **CRFacturacion1**: posible código muerto
- **CRreporte_persona**: usa `sa`/password hardcodeado en `AppSettings`
- Los reportes de almacén filtran por `ubicacion = 'CLIENTE'` — si el campo se renombra, dejan de funcionar
- `AplicarConexionReporte` modifica `tb.Location` dinámicamente — cualquier cambio de naming/schema en BD rompe los reportes
- No hay trazabilidad de qué vista SQL exacta usa cada `.rpt` (embebida en el binario, no en código VB)
