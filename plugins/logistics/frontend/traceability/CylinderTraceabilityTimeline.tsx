import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";
import { Skeleton } from "@systutor/shell/ui/skeleton";
import { getCylinderStateLabel } from "../CylinderStateBadge";
import { getCylinderTraceability, type LogisticsCylinderTraceability, type LogisticsTraceabilityEvent } from "../api/traceability";
import { formatDateTime } from "../cylinders/utils/formatters";

const EVENT_TYPE_LABELS: Record<string, string> = {
  created: "Creación",
  state_change: "Cambio de estado",
  scan: "Escaneo",
  loaded: "Carga",
  unloaded: "Descarga",
  moved: "Movimiento",
  hydrotest: "PH",
  retimbrado: "Retimbrado",
  service: "Servicio",
  warranty: "Garantía",
  ownership: "Custodia",
  label_print: "Etiqueta",
  weight_updated: "Peso",
  medical_flag_changed: "Medicinal",
  contract_assigned: "Contrato",
  contract_released: "Contrato",
};

function readText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function renderDetail(event: LogisticsTraceabilityEvent) {
  if (event.event_type === "state_change") {
    const fromState = readText(event.metadata.from_state);
    const toState = readText(event.metadata.to_state);
    return `${fromState ? getCylinderStateLabel(fromState) : "Inicio"} -> ${toState ? getCylinderStateLabel(toState) : "-"}`;
  }
  return event.description;
}

function renderOrigin(event: LogisticsTraceabilityEvent) {
  const origin = readText(event.metadata.origin);
  return origin || "-";
}

function renderNotes(event: LogisticsTraceabilityEvent) {
  const notes = readText(event.metadata.notes);
  if (notes) {
    return notes;
  }
  if (event.event_type === "scan") {
    const lat = readNumber(event.metadata.gps_lat);
    const lng = readNumber(event.metadata.gps_lng);
    const result = readText(event.metadata.result);
    if (lat !== null && lng !== null) {
      return `GPS ${lat}, ${lng}${result ? ` · ${result}` : ""}`;
    }
    return result || "-";
  }
  if (event.event_type === "medical_flag_changed") {
    const oldValue = event.metadata.old_value;
    const newValue = event.metadata.new_value;
    if (typeof oldValue === "boolean" && typeof newValue === "boolean") {
      return `${String(oldValue).toLowerCase()} -> ${String(newValue).toLowerCase()}`;
    }
  }
  if (event.event_type === "label_print") {
    const copies = readNumber(event.metadata.copies);
    return copies !== null ? `${copies} copias` : "-";
  }
  return "-";
}

function buildSearchText(event: LogisticsTraceabilityEvent) {
  return [
    event.event_type,
    event.description,
    event.actor ?? "",
    renderOrigin(event),
    renderNotes(event),
    JSON.stringify(event.metadata),
  ]
    .join(" ")
    .toLowerCase();
}

export function CylinderTraceabilityTimeline({ cylinderId }: { cylinderId: string }) {
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [data, setData] = useState<LogisticsCylinderTraceability | null>(null);
  const [allEvents, setAllEvents] = useState<LogisticsTraceabilityEvent[]>([]);

  const fetchPage = useCallback(
    async (pageNum: number) => {
      if (pageNum === 1) {
        setLoading(true);
        setError(null);
      } else {
        setLoadingMore(true);
      }
      try {
        const result = await getCylinderTraceability(cylinderId, pageNum, 20);
        if (pageNum === 1) {
          setAllEvents(result.events);
        } else {
          setAllEvents((prev) => [...prev, ...result.events]);
        }
        setData(result);
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : "No se pudo cargar la trazabilidad.");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [cylinderId]
  );

  useEffect(() => {
    setSearch("");
    setAllEvents([]);
    setData(null);
    fetchPage(1);
  }, [cylinderId, fetchPage]);

  const filteredEvents = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return allEvents;
    }
    return allEvents.filter((event) => buildSearchText(event).includes(normalizedSearch));
  }, [allEvents, search]);

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return <Alert title="No se pudo cargar la trazabilidad">{error}</Alert>;
  }

  return (
    <div className="space-y-4">
      <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar en trazabilidad" />
      <DataTable
        columns={[
          { key: "when", header: "Fecha", render: (row) => formatDateTime(row.timestamp) },
          {
            key: "type",
            header: "Tipo",
            render: (row) => EVENT_TYPE_LABELS[row.event_type] || row.event_type,
          },
          {
            key: "detail",
            header: "Detalle",
            render: (row) => <span className="text-sm text-foreground">{renderDetail(row)}</span>,
          },
          { key: "origin", header: "Origen", render: (row) => renderOrigin(row) },
          { key: "notes", header: "Notas", render: (row) => renderNotes(row) },
        ]}
        rows={filteredEvents}
        rowKey={(row) => `${row.timestamp}-${row.event_type}-${row.description}`}
        emptyMessage="Aún no hay trazas registradas."
      />
      {data && data.pagination.page < data.pagination.total_pages ? (
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => fetchPage(data.pagination.page + 1)} disabled={loadingMore}>
            {loadingMore ? "Cargando..." : "Cargar más"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
