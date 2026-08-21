// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { LocationPicker } from "@systutor/shell/ui/location-picker";
import { DEFAULT_MAP_CENTER } from "../../components/route-builder/map-defaults";
import { Field } from "../utils/formatters";

interface ScanDialogProps {
  isScanOpen: boolean;
  setIsScanOpen: (open: boolean) => void;
  scanForm: any;
  setScanForm: (form: any) => void;
  handleScan: (event: any) => void;
  scanMutation: { isPending: boolean };
  fallbackMessage?: string | null;
  onOpenRegisterFallback?: () => void;
}

export function ScanDialog({
    isScanOpen,
    setIsScanOpen,
    scanForm,
    setScanForm,
    handleScan,
    scanMutation,
    fallbackMessage,
    onOpenRegisterFallback,
}: ScanDialogProps) {
  return (
<Dialog open={isScanOpen} title="Escaneo en campo" description="Procesa un escaneo con validación ADR/PH y GPS." maxWidthClassName="max-w-[1200px]" onClose={() => setIsScanOpen(false)}>
  <form className="space-y-4" onSubmit={handleScan}>
    <div className="grid gap-3 md:grid-cols-3">
      <Field label="Movimiento (opcional)"><Input placeholder="Se auto-asigna del último movimiento del envase" value={scanForm.movement_id} onChange={(event) => setScanForm((current) => ({ ...current, movement_id: event.target.value }))} /></Field>
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
    </div>
    <LocationPicker
      value={scanForm.gps_lat && scanForm.gps_lng ? { lat: Number(scanForm.gps_lat), lng: Number(scanForm.gps_lng) } : null}
      onChange={(location) => setScanForm((current) => ({ ...current, gps_lat: location.lat.toString(), gps_lng: location.lng.toString() }))}
      height={500}
      defaultCenter={DEFAULT_MAP_CENTER}
    />
    <div className="flex justify-end gap-2">
      {fallbackMessage && onOpenRegisterFallback ? (
        <Button type="button" variant="secondary" onClick={onOpenRegisterFallback}>
          Registrar envase
        </Button>
      ) : null}
      <Button type="button" variant="secondary" onClick={() => setIsScanOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={scanMutation.isPending}>Procesar escaneo</Button>
    </div>
  </form>
</Dialog>
  );
}
