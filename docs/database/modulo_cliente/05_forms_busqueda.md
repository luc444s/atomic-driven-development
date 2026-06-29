# Módulo Clientes — Forms de Búsqueda

## 1. FBusPacPRO.vb (282 líneas)

**Propósito:** Búsqueda modal de clientes. Devuelve al formulario `FrmRegClientePRO`.

### Columnas del ListView (20 columnas)
```
CÓDIGO(80), CLIENTE(350), DNI(80), RUC(90), TELEFONO(80), CORREO(80),
DIRECCION(0), LC(60), DIASCRED(100), GARANTIA(0), RETENEDOR(0), Agente(100),
Id_Ag(0), Comisión(0), Enviar(0), IdClaveOP(0), TipoFacturacion(0),
DocumentoPrincipal(0), IdFormaPago(0), Intracomunitario(0)
```

### SP usado
```vb.net
obj.BuscarClientProvxnom(1, txtdescripcion.Text)  ' tipo=1 (clientes), límite 150
```

### DobleClick / Enter
Devuelve a `FrmRegClientePRO`:
```vb.net
.TxtCodPac.Text = codigo (Enabled = False)
.txtCliente, .txtDni, .txtruc, .TxtTel, .txtemail, .txtdir
.NumericUpDown1LC, .Diascred
.ChekEnviar.Checked
.RB1conGarantia / .RB2sinGarantia
.CBAgente.Text, .LblidAgente.Text, .NUDcomisión.Text
.CBclaveOP.Text, .CBtipoFac.Text, .CBDocumentoPrincipal.Text
.LblIDFormaPago.Text
.ChkIntracomunitario.Checked
```

---

## 2. FBusPacPLUS.vb (233 líneas)

**Propósito:** Búsqueda modal. Devuelve a `FrmRegClientePLUS`.

### Columnas (solo 16 columnas — sin datos fiscales)
Mismas hasta `Enviar(0)`. **Sin** IdClaveOP, TipoFacturacion, DocumentoPrincipal, IdFormaPago, Intracomunitario.

### SP usado
```vb.net
obj.BuscarClientProvxnom(1, txtdescripcion.Text)  ' mismo SP que PRO
```

### BUG Documentado (línea 153)
```vb.net
' El KeyPress apunta a FrmRegClientePRO en lugar de FrmRegClientePLUS:
With FrmRegClientePRO  ' ← BUG
```

---

## 3. FBusPacPROcr.vb (291 líneas)

**Propósito:** Búsqueda modal para Costa Rica. Devuelve a `FrmCatClientes`.

### SP usado (DIFERENTE)
```vb.net
obj.BuscarClientexnomFiscal(1, txtdescripcion.Text)  ' ← NO es BuscarClientProvxnom
```

### Columnas
Mismas 20 que FBusPacPRO.

### DobleClick
Devuelve a `FrmCatClientes` con todos los campos incluyendo fiscales.

---

## 4. FBusPacProv.vb (164 líneas)

**Propósito:** Búsqueda de proveedores (Cod_TipoPersona=2). Devuelve a `FrmCatProveedores`.

### Columnas
```
CÓDIGO(60), CLIENTE(200), DNI(0), RUC(100), TELEFONO(100), EMAIL(180),
DIRECCION(230), DIA VISITA(80)
```

### SP usado
```vb.net
obj.BuscarClientProvxnom(4, txtdescripcion.Text)  ' tipo=4 (proveedores), límite 150
```

### DobleClick
Devuelve a `FrmCatProveedores` con:
```vb.net
.TxtCodPac, .txtCliente, .txtDni, .txtruc, .TxtTel, .txtemail, .txtdir, .cbdv
```

---

## Resumen de SPs de Búsqueda

| Form | SP | Tipo persona | Formulario destino |
|------|-----|-------------|-------------------|
| FBusPacPRO | `BuscarClientProvxnom(1, texto)` | Clientes (1) | FrmRegClientePRO |
| FBusPacPLUS | `BuscarClientProvxnom(1, texto)` | Clientes (1) | FrmRegClientePLUS (**BUG** apunta a PRO) |
| FBusPacPROcr | `BuscarClientexnomFiscal(1, texto)` | Clientes (1) | FrmCatClientes |
| FBusPacProv | `BuscarClientProvxnom(4, texto)` | Proveedores (4) | FrmCatProveedores |
