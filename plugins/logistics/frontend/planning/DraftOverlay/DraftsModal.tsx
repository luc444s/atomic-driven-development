import { useState, useMemo } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Dialog } from "@systutor/shell/ui/dialog";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Pagination } from "@systutor/shell/ui/pagination";
import { Button } from "@systutor/shell/ui/button";
import { Input } from "@systutor/shell/ui/input";
import { listCotizaciones, type QuoteDraftListItem } from "../../../../../plugins/ventas/cotizacion/frontend/api";
import type { DataTableColumn } from "@systutor/shell/ui/data-table";

interface DraftsModalProps {
  open: boolean;
  dateFrom: string;
  dateTo: string;
  onClose: () => void;
  onConfirm: (id: string) => void;
  onPlanificar: (id: string) => void;
}

const PAGE_SIZE = 20;
const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export function DraftsModal({ open, dateFrom, dateTo, onClose, onConfirm, onPlanificar }: DraftsModalProps) {
  const [search, setSearch] = useState("");
  const [monthFilter, setMonthFilter] = useState("");
  const [dayFilter, setDayFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data: drafts = [] } = useQuery({
    queryKey: ["planning", "drafts-modal", dateFrom, dateTo],
    queryFn: () =>
      listCotizaciones({
        status: "DRAFT",
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: open,
    refetchOnWindowFocus: false,
    staleTime: 15_000,
  });

  const { data: confirmed = [] } = useQuery({
    queryKey: ["planning", "drafts-modal", "confirmed", dateFrom, dateTo],
    queryFn: () =>
      listCotizaciones({
        status: "CONFIRMED",
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: open,
    refetchOnWindowFocus: false,
    staleTime: 15_000,
  });

  const all = useMemo(() => [...drafts, ...confirmed], [drafts, confirmed]);

  const filtered = useMemo(() => {
    return all.filter((d) => {
      if (search) {
        const q = search.toLowerCase();
        const haystack = [d.id, d.customer_name ?? "", d.delivery_date].join(" ").toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      if (monthFilter) {
        const m = new Date(d.delivery_date + "T00:00:00").getMonth() + 1;
        if (String(m) !== monthFilter) return false;
      }
      if (dayFilter) {
        const dNum = new Date(d.delivery_date + "T00:00:00").getDate();
        if (String(dNum) !== dayFilter) return false;
      }
      return true;
    });
  }, [all, search, monthFilter, dayFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = useMemo(
    () => filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filtered, page],
  );

  const columns: DataTableColumn<QuoteDraftListItem>[] = [
    {
      key: "id",
      header: "#",
      className: "w-24",
      render: (d) => <span className="font-mono text-primary/70">{d.id.slice(0, 4).toUpperCase()}</span>,
    },
    {
      key: "customer",
      header: "Cliente",
      render: (d) => d.customer_name ?? "—",
    },
    {
      key: "date",
      header: "Fecha",
      className: "w-28",
      render: (d) => d.delivery_date,
    },
    {
      key: "status",
      header: "Estado",
      className: "w-24",
      render: (d) => (
        <span className={d.status === "CONFIRMED" ? "text-emerald-400" : "text-yellow-400/80"}>
          {d.status === "CONFIRMED" ? "⚡ " : ""}{d.status}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      className: "w-24",
      render: (d) =>
        d.status === "CONFIRMED" ? (
          <Button
            variant="primary"
            className="!text-[10px] !px-2 !py-0.5 h-5"
            onClick={() => onPlanificar(d.id)}
          >
            Planificar
          </Button>
        ) : (
          <Button
            variant="secondary"
            className="!text-[10px] !px-2 !py-0.5 h-5"
            onClick={() => onConfirm(d.id)}
          >
            Confirmar
          </Button>
        ),
    },
  ];

  const availableDays = useMemo(() => {
    const days = new Set<number>();
    for (const d of all) {
      const dayNum = new Date(d.delivery_date + "T00:00:00").getDate();
      days.add(dayNum);
    }
    return Array.from(days).sort((a, b) => a - b);
  }, [all]);

  return (
    <Dialog
      open={open}
      title={`Demanda pendiente (${filtered.length})`}
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="space-y-4">
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Buscar por cliente, #CTZ..."
            />
          </div>
          <select
            value={monthFilter}
            onChange={(e) => { setMonthFilter(e.target.value); setPage(1); }}
            className="w-32 rounded-md border border-input bg-surface px-2 py-2 text-sm text-foreground outline-none h-9"
          >
            <option value="">Mes</option>
            {MONTHS.map((name, i) => (
              <option key={i} value={String(i + 1)}>{name}</option>
            ))}
          </select>
          <select
            value={dayFilter}
            onChange={(e) => { setDayFilter(e.target.value); setPage(1); }}
            className="w-16 rounded-md border border-input bg-surface px-2 py-2 text-sm text-foreground outline-none h-9"
          >
            <option value="">Día</option>
            {availableDays.map((d) => (
              <option key={d} value={String(d)}>{d}</option>
            ))}
          </select>
        </div>

        <DataTable
          columns={columns}
          rows={pageItems}
          rowKey={(d) => d.id}
          emptyMessage="Sin demanda pendiente."
          dense
        />

        {totalPages > 1 && (
          <Pagination page={page} totalPages={totalPages} onChange={setPage} />
        )}
      </div>
    </Dialog>
  );
}
