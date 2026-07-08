#!/usr/bin/env python3
"""Regenerate all 7 small dialog components with clean props."""
from pathlib import Path

BASE = Path("plugins/logistics/frontend/cylinders/dialogs")

TEMPLATE = """// Auto-generado por split-tsx.py
{imports}

interface {name}Props {{
{props_iface}
}}

export function {name}({{
{props_dest}
}}: {name}Props) {{
  return (
{jsx}
  );
}}
"""

DIALOGS = {}

DIALOGS["HydrotestDialog"] = {
    "props": [
        "isHydrotestOpen: boolean",
        "setIsHydrotestOpen: (open: boolean) => void",
        "hydrotestForm: any",
        "setHydrotestForm: (form: any) => void",
        "handleHydrotest: (event: any) => void",
        "hydrotestMutation: { isPending: boolean }",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input, Textarea } from "../../../apps/web/src/shared/ui/input"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isHydrotestOpen} title="Registrar PH" description="Actualiza la prueba hidrostática vigente del envase." onClose={() => setIsHydrotestOpen(false)}>
  <form className="space-y-4" onSubmit={handleHydrotest}>
    <div className="grid gap-3 md:grid-cols-2">
      <Field label="Fecha de PH"><Input type="date" value={hydrotestForm.test_date} onChange={(event) => setHydrotestForm((current) => ({ ...current, test_date: event.target.value }))} /></Field>
      <Field label="Estado"><Input value={hydrotestForm.status} onChange={(event) => setHydrotestForm((current) => ({ ...current, status: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={hydrotestForm.notes} onChange={(event) => setHydrotestForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsHydrotestOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={hydrotestMutation.isPending}>Registrar PH</Button>
    </div>
  </form>
</Dialog>""",
}

DIALOGS["WarrantyDialog"] = {
    "props": [
        "isWarrantyOpen: boolean",
        "setIsWarrantyOpen: (open: boolean) => void",
        "warrantyForm: any",
        "setWarrantyForm: (form: any) => void",
        "handleWarranty: (event: any) => void",
        "warrantyMutation: { isPending: boolean }",
        "setIsWarrantyCustomerSearchOpen: (open: boolean) => void",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input, Textarea } from "../../../apps/web/src/shared/ui/input"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isWarrantyOpen} title="Registrar garantía" description="Asocia la garantía comercial del envase." onClose={() => setIsWarrantyOpen(false)}>
  <form className="space-y-4" onSubmit={handleWarranty}>
    <div className="grid gap-3 md:grid-cols-2">
      <Field label="Cliente">
        <Button type="button" variant="secondary" onClick={() => setIsWarrantyCustomerSearchOpen(true)}>
          {warrantyForm.customer_name ? `$warrantyForm.customer_name ($warrantyForm.customer_id)` : "Seleccionar cliente"}
        </Button>
      </Field>
      <Field label="Tipo"><Input value={warrantyForm.warranty_type} onChange={(event) => setWarrantyForm((current) => ({ ...current, warranty_type: event.target.value }))} /></Field>
    </div>
    <Field label="Detalle"><Textarea rows={4} value={warrantyForm.description} onChange={(event) => setWarrantyForm((current) => ({ ...current, description: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsWarrantyOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={warrantyMutation.isPending}>Registrar garantía</Button>
    </div>
  </form>
</Dialog>""",
}

DIALOGS["RetimbradoDialog"] = {
    "props": [
        "isRetimbradoOpen: boolean",
        "setIsRetimbradoOpen: (open: boolean) => void",
        "retimbradoForm: any",
        "setRetimbradoForm: (form: any) => void",
        "handleRetimbrado: (event: any) => void",
        "retimbradoMutation: { isPending: boolean }",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input, Textarea } from "../../../apps/web/src/shared/ui/input"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isRetimbradoOpen} title="Registrar retimbrado" description="Carga la ficha técnica del retimbrado del envase." onClose={() => setIsRetimbradoOpen(false)}>
  <form className="space-y-4" onSubmit={handleRetimbrado}>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <Field label="Fecha"><Input type="date" value={retimbradoForm.retimbrado_date} onChange={(event) => setRetimbradoForm((current) => ({ ...current, retimbrado_date: event.target.value }))} /></Field>
      <Field label="Código fabricación"><Input value={retimbradoForm.manufacture_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_code: event.target.value }))} /></Field>
      <Field label="Año"><Input type="number" value={retimbradoForm.manufacture_year} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_year: event.target.value }))} /></Field>
      <Field label="Nro bombona"><Input value={retimbradoForm.serial_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, serial_number: event.target.value }))} /></Field>
      <Field label="Peso origen"><Input type="number" value={retimbradoForm.weight_origin} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_origin: event.target.value }))} /></Field>
      <Field label="Peso actual"><Input type="number" value={retimbradoForm.weight_current} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_current: event.target.value }))} /></Field>
      <Field label="Presión servicio"><Input type="number" value={retimbradoForm.service_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, service_pressure: event.target.value }))} /></Field>
      <Field label="Presión prueba"><Input type="number" value={retimbradoForm.test_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, test_pressure: event.target.value }))} /></Field>
      <Field label="Nro aprobación"><Input value={retimbradoForm.approval_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, approval_number: event.target.value }))} /></Field>
      <Field label="Clase peligro"><Input value={retimbradoForm.danger_class} onChange={(event) => setRetimbradoForm((current) => ({ ...current, danger_class: event.target.value }))} /></Field>
      <Field label="Marcado 1"><Input value={retimbradoForm.marking1} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking1: event.target.value }))} /></Field>
      <Field label="Marcado 2"><Input value={retimbradoForm.marking2} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking2: event.target.value }))} /></Field>
      <Field label="Formato bulto"><Input value={retimbradoForm.package_format} onChange={(event) => setRetimbradoForm((current) => ({ ...current, package_format: event.target.value }))} /></Field>
      <Field label="Transporte"><Input type="number" value={retimbradoForm.transport_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, transport_code: event.target.value }))} /></Field>
      <Field label="Etiqueta ADR"><Input value={retimbradoForm.adr_label} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_label: event.target.value }))} /></Field>
      <Field label="Túnel ADR"><Input value={retimbradoForm.adr_tunnel} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_tunnel: event.target.value }))} /></Field>
      <Field label="Nro ONU"><Input value={retimbradoForm.un_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, un_number: event.target.value }))} /></Field>
      <Field label="Registro alimentario"><Input value={retimbradoForm.food_registry} onChange={(event) => setRetimbradoForm((current) => ({ ...current, food_registry: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={retimbradoForm.notes} onChange={(event) => setRetimbradoForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsRetimbradoOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={retimbradoMutation.isPending}>Registrar retimbrado</Button>
    </div>
  </form>
</Dialog>""",
}

DIALOGS["ServiceDialog"] = {
    "props": [
        "isServiceOpen: boolean",
        "setIsServiceOpen: (open: boolean) => void",
        "serviceForm: any",
        "setServiceForm: (form: any) => void",
        "handleService: (event: any) => void",
        "serviceMutation: { isPending: boolean }",
        "serviceTypesQuery: { data: Array<{ id: string; name: string }> }",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input, Textarea } from "../../../apps/web/src/shared/ui/input"',
        '{ Select } from "../../../apps/web/src/shared/ui/select"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isServiceOpen} title="Registrar servicio" description="Asocia un servicio operativo sobre el envase." onClose={() => setIsServiceOpen(false)}>
  <form className="space-y-4" onSubmit={handleService}>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <Field label="Tipo servicio">
        <Select value={serviceForm.service_type_id} onChange={(value) => setServiceForm((current) => ({ ...current, service_type_id: value }))}
          placeholder="Selecciona"
          options={(serviceTypesQuery.data ?? []).map((item) => ({ value: item.id, label: item.name }))} />
      </Field>
      <Field label="Estado"><Input value={serviceForm.status} onChange={(event) => setServiceForm((current) => ({ ...current, status: event.target.value }))} /></Field>
      <Field label="Inicio"><Input type="datetime-local" value={serviceForm.start_date} onChange={(event) => setServiceForm((current) => ({ ...current, start_date: event.target.value }))} /></Field>
      <Field label="Fin"><Input type="datetime-local" value={serviceForm.end_date} onChange={(event) => setServiceForm((current) => ({ ...current, end_date: event.target.value }))} /></Field>
      <Field label="Precio compra"><Input type="number" value={serviceForm.purchase_price} onChange={(event) => setServiceForm((current) => ({ ...current, purchase_price: event.target.value }))} /></Field>
      <Field label="Precio venta"><Input type="number" value={serviceForm.sale_price} onChange={(event) => setServiceForm((current) => ({ ...current, sale_price: event.target.value }))} /></Field>
      <Field label="Stock ingreso"><Input type="number" value={serviceForm.stock_in} onChange={(event) => setServiceForm((current) => ({ ...current, stock_in: event.target.value }))} /></Field>
      <Field label="Stock egreso"><Input type="number" value={serviceForm.stock_out} onChange={(event) => setServiceForm((current) => ({ ...current, stock_out: event.target.value }))} /></Field>
      <Field label="Grupo"><Input value={serviceForm.group_code} onChange={(event) => setServiceForm((current) => ({ ...current, group_code: event.target.value }))} /></Field>
      <Field label="Desc %"><Input type="number" value={serviceForm.discount_pct} onChange={(event) => setServiceForm((current) => ({ ...current, discount_pct: event.target.value }))} /></Field>
      <Field label="Desc monto"><Input type="number" value={serviceForm.discount_amount} onChange={(event) => setServiceForm((current) => ({ ...current, discount_amount: event.target.value }))} /></Field>
      <Field label="Total"><Input type="number" value={serviceForm.total_amount} onChange={(event) => setServiceForm((current) => ({ ...current, total_amount: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={serviceForm.notes} onChange={(event) => setServiceForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsServiceOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={serviceMutation.isPending}>Registrar servicio</Button>
    </div>
  </form>
</Dialog>""",
}

DIALOGS["PrintLabelDialog"] = {
    "props": [
        "isPrintLabelOpen: boolean",
        "setIsPrintLabelOpen: (open: boolean) => void",
        "printLabelForm: any",
        "setPrintLabelForm: (form: any) => void",
        "handlePrintLabel: (event: any) => void",
        "printLabelMutation: { isPending: boolean }",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input, Textarea } from "../../../apps/web/src/shared/ui/input"',
        '{ Select } from "../../../apps/web/src/shared/ui/select"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isPrintLabelOpen} title="Imprimir etiqueta" description="Registra la impresión operativa de la etiqueta del envase." onClose={() => setIsPrintLabelOpen(false)}>
  <form className="space-y-4" onSubmit={handlePrintLabel}>
    <div className="grid gap-3 md:grid-cols-3">
      <Field label="Origen">
        <Select value={printLabelForm.origin} onChange={(value) => setPrintLabelForm((current) => ({ ...current, origin: value }))}
          options={[
            { value: "ALTA", label: "ALTA" },
            { value: "REIMPRESION", label: "REIMPRESION" },
            { value: "PLUS", label: "PLUS" },
          ]} />
      </Field>
      <Field label="Impresora"><Input value={printLabelForm.printer_name} onChange={(event) => setPrintLabelForm((current) => ({ ...current, printer_name: event.target.value }))} /></Field>
      <Field label="Copias"><Input type="number" value={printLabelForm.copies} onChange={(event) => setPrintLabelForm((current) => ({ ...current, copies: event.target.value }))} /></Field>
    </div>
    <Field label="Motivo"><Textarea rows={3} value={printLabelForm.reason} onChange={(event) => setPrintLabelForm((current) => ({ ...current, reason: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsPrintLabelOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={printLabelMutation.isPending}>Registrar impresión</Button>
    </div>
  </form>
</Dialog>""",
}

DIALOGS["TransitionDialog"] = {
    "props": [
        "isTransitionOpen: boolean",
        "setIsTransitionOpen: (open: boolean) => void",
        "nextState: string",
        "setNextState: (value: string) => void",
        "handleTransition: () => void",
        "transitionMutation: { isPending: boolean }",
        "transitionsQuery: { data: Array<{ to_state: string }> }",
        "getCylinderStateLabel: (state: string) => string",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Select } from "../../../apps/web/src/shared/ui/select"',
    ],
    "jsx": """<Dialog open={isTransitionOpen} title="Transición operativa" description="Aplica la siguiente transición válida del state machine." onClose={() => setIsTransitionOpen(false)}>
  <div className="space-y-4">
    <Select
      value={nextState}
      onChange={(value) => setNextState(value)}
      placeholder="Selecciona estado destino"
      options={(transitionsQuery.data ?? []).map((item) => ({
        value: item.to_state,
        label: getCylinderStateLabel(item.to_state),
      }))}
    />
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsTransitionOpen(false)}>
        Cancelar
      </Button>
      <Button
        onClick={async () => {
          await handleTransition();
          setIsTransitionOpen(false);
        }}
        disabled={!nextState || transitionMutation.isPending}
      >
        Aplicar transición
      </Button>
    </div>
  </div>
</Dialog>""",
}

DIALOGS["ScanDialog"] = {
    "props": [
        "isScanOpen: boolean",
        "setIsScanOpen: (open: boolean) => void",
        "scanForm: any",
        "setScanForm: (form: any) => void",
        "handleScan: (event: any) => void",
        "scanMutation: { isPending: boolean }",
    ],
    "imports": [
        '{ Dialog } from "../../../apps/web/src/shared/ui/dialog"',
        '{ Button } from "../../../apps/web/src/shared/ui/button"',
        '{ Input } from "../../../apps/web/src/shared/ui/input"',
        '{ Select } from "../../../apps/web/src/shared/ui/select"',
        '{ Field } from "../utils/formatters"',
    ],
    "jsx": """<Dialog open={isScanOpen} title="Escaneo en campo" description="Procesa un escaneo con validación ADR/PH y GPS." onClose={() => setIsScanOpen(false)}>
  <form className="space-y-4" onSubmit={handleScan}>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <Field label="Movimiento"><Input value={scanForm.movement_id} onChange={(event) => setScanForm((current) => ({ ...current, movement_id: event.target.value }))} /></Field>
      <Field label="Barcode / serie"><Input value={scanForm.barcode_serial} onChange={(event) => setScanForm((current) => ({ ...current, barcode_serial: event.target.value }))} /></Field>
      <Field label="Servicio">
        <Select value={scanForm.service_type} onChange={(value) => setScanForm((current) => ({ ...current, service_type: value }))}
          options={[
            { value: "VENTA", label: "VENTA" },
            { value: "CANJE_ENTREGA", label: "CANJE_ENTREGA" },
            { value: "CANJE_RECOJO", label: "CANJE_RECOJO" },
            { value: "ALQUILER", label: "ALQUILER" },
            { value: "DEVOLUCION", label: "DEVOLUCION" },
            { value: "RECHAZO", label: "RECHAZO" },
            { value: "SPOT", label: "SPOT" },
          ]} />
      </Field>
      <Field label="GPS lat"><Input type="number" value={scanForm.gps_lat} onChange={(event) => setScanForm((current) => ({ ...current, gps_lat: event.target.value }))} /></Field>
      <Field label="GPS lng"><Input type="number" value={scanForm.gps_lng} onChange={(event) => setScanForm((current) => ({ ...current, gps_lng: event.target.value }))} /></Field>
    </div>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsScanOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={scanMutation.isPending}>Procesar escaneo</Button>
    </div>
  </form>
</Dialog>""",
}

for name, dlg in DIALOGS.items():
    imports_str = "\n".join(f"import {imp};" for imp in dlg["imports"])
    props_iface = "\n".join(f"  {p};" for p in dlg["props"])
    props_dest = ",\n".join(f"    {p.split(':')[0].strip()}" for p in dlg["props"]) + ","
    jsx = dlg["jsx"]

    content = TEMPLATE.format(
        name=name,
        imports=imports_str,
        props_iface=props_iface,
        props_dest=props_dest,
        jsx=jsx,
    )

    path = BASE / f"{name}.tsx"
    path.write_text(content)
    print(f"Regenerated: {path.name} ({len(dlg['props'])} props)")

print("\nDone!")
