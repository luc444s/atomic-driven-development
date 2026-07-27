import { useState, useCallback } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Textarea } from "../../../../../apps/web/src/shared/ui/textarea";
import { CustomerSelect } from "./CustomerSelect";
import { ProductLinesEditor } from "./ProductLinesEditor";
import { DateTimePicker } from "./DateTimePicker";
import { VehicleSelect } from "./VehicleSelect";
import { prepareQuote } from "../shared/application/prepareQuote";
import { createQuote } from "../shared/application/createQuote";
import { QuotePreview } from "../components/QuotePreview";
import type { QuoteCommand } from "../shared/types/commands";
import type { QuoteDraftDTO } from "../shared/types";
import type { ProductLine } from "./ProductLinesEditor";

interface CotizacionFormProps {
  onDraftCreated: () => void;
}

type FormState = "editing" | "previewing" | "creating";

export function CotizacionForm({ onDraftCreated }: CotizacionFormProps) {
  const [phase, setPhase] = useState<FormState>("editing");
  const [customerId, setCustomerId] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [lines, setLines] = useState<ProductLine[]>([
    { key: "initial", productId: "", productName: "", quantity: 1 },
  ]);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [vehiclePlate, setVehiclePlate] = useState("");
  const [conditions, setConditions] = useState("");
  const [preview, setPreview] = useState<QuoteDraftDTO | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isValid =
    customerId.trim() !== "" &&
    lines.some((l) => l.productId.trim() !== "" && l.quantity > 0) &&
    date.trim() !== "";

  const buildQuoteCommand = useCallback((): QuoteCommand => {
    return {
      action: "cotizar",
      dryRun: false,
      cliente: customerName,
      items: lines
        .filter((l) => l.productId.trim() !== "" && l.quantity > 0)
        .map((l) => ({ cantidad: l.quantity, producto: l.productName })),
      fecha: date,
      hora: time || null,
      vehiculo: vehiclePlate || null,
      condiciones: conditions || null,
    };
  }, [customerName, lines, date, time, vehiclePlate, conditions]);

  const handlePreview = useCallback(async () => {
    if (!isValid) return;
    setPhase("previewing");
    setError(null);
    try {
      const cmd = buildQuoteCommand();
      const result = await prepareQuote(cmd);
      setPreview(result.preview);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al previsualizar");
      setPhase("editing");
    }
  }, [isValid, buildQuoteCommand]);

  const handleReset = useCallback(() => {
    setPhase("editing");
    setCustomerId("");
    setCustomerName("");
    setLines([{ key: "initial", productId: "", productName: "", quantity: 1 }]);
    setDate("");
    setTime("");
    setVehicleId("");
    setVehiclePlate("");
    setConditions("");
    setPreview(null);
    setError(null);
  }, []);

  const handleCreate = useCallback(async () => {
    setPhase("creating");
    setError(null);
    try {
      const cmd = buildQuoteCommand();
      await createQuote(cmd);
      onDraftCreated();
      handleReset();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear cotización");
      setPhase("editing");
      setPreview(null);
    }
  }, [buildQuoteCommand, onDraftCreated, handleReset]);

  return (
    <form
      className="space-y-6 p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (phase === "editing") handlePreview();
        else if (phase === "previewing" && preview) handleCreate();
      }}
    >
      {error && (
        <Alert title="Error">{error}</Alert>
      )}

      <CustomerSelect
        value={customerId}
        onChange={(id, name) => {
          setCustomerId(id);
          setCustomerName(name);
        }}
      />

      <ProductLinesEditor value={lines} onChange={setLines} />

      <DateTimePicker
        dateValue={date}
        timeValue={time}
        onDateChange={setDate}
        onTimeChange={setTime}
      />

      <VehicleSelect
        value={vehicleId}
        onChange={(id, plate) => {
          setVehicleId(id);
          setVehiclePlate(plate);
        }}
      />

      <label className="block space-y-2 text-sm text-foreground">
        <span>Condiciones (opcional)</span>
        <Textarea
          value={conditions}
          onChange={(e) => setConditions(e.target.value)}
          rows={2}
          placeholder="Ej: pago contra entrega"
        />
      </label>

      {phase === "previewing" && preview && (
        <div className="rounded-md border border-border p-4">
          <p className="mb-3 text-sm font-medium text-foreground">Previsualización</p>
          <QuotePreview draft={preview} />
        </div>
      )}

      <div className="flex justify-end gap-3">
        {phase === "previewing" && preview && (
          <Button type="button" variant="secondary" onClick={() => { setPhase("editing"); setPreview(null); }}>
            Cancelar
          </Button>
        )}
        <Button
          type="submit"
              disabled={!isValid || phase === "creating"}
        >
          {phase === "creating"
            ? "Creando..."
            : phase === "previewing"
            ? "Crear cotización"
            : "Previsualizar"}
        </Button>
      </div>
      </form>
  );
}
