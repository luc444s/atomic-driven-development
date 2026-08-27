import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { useState } from "react";
import { getCylinderHistory } from "../api";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";
import { Input } from "@systutor/shell/ui/input";

const CUSTODY_BADGE: Record<string, string> = {
  PENDIENTE: "border-warning/30 bg-warning/10 text-warning",
  EN_CUSTODIA: "border-primary/30 bg-primary/10 text-primary",
};

const DIFFERENCE_BADGE: Record<string, string> = {
  FALTANTE: "border-destructive/30 bg-destructive/10 text-destructive",
  DANO: "border-destructive/30 bg-destructive/10 text-destructive",
  SOBRANTE: "border-warning/30 bg-warning/10 text-warning",
};

function VigenciaBadge({ nextTestDate, result }: { nextTestDate: string | null; result: string | null }) {
  if (result === "APROBADO" && nextTestDate) {
    const expired = new Date(nextTestDate) < new Date();
    return (
      <Badge
        className={
          expired
            ? "border-destructive/30 bg-destructive/10 text-destructive"
            : "border-warning/30 bg-warning/10 text-warning"
        }
      >
        {expired ? "Vigencia vencida" : "Vigente"}: {nextTestDate}
      </Badge>
    );
  }
  if (result) {
    return <Badge>{result}</Badge>;
  }
  return null;
}

export function CylinderHistoryPage() {
  const [serial, setSerial] = useState("");
  const [submitted, setSubmitted] = useState("");

  const historyQuery = useQuery({
    queryKey: ["compras", "cylinder-history", submitted],
    queryFn: () => getCylinderHistory(submitted),
    enabled: submitted !== "",
  });

  const history = submitted !== "" ? historyQuery.data : undefined;
  const error =
    historyQuery.error instanceof Error
      ? historyQuery.error.message
      : historyQuery.error
        ? "Error al consultar el historial"
        : null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="gap-3">
          <div>
            <CardTitle>Historial del envase</CardTitle>
            <CardDescription>
              Consulta consolidada por serial: despachos, recepciones y servicios con su vigencia legal.
            </CardDescription>
          </div>
          <form
            className="flex max-w-md gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setSubmitted(serial.trim());
            }}
          >
            <Input
              value={serial}
              onChange={(e) => setSerial(e.target.value)}
              placeholder="Serial (ej. CIL-0001)"
            />
            <Button type="submit" disabled={serial.trim() === "" || historyQuery.isFetching}>
              Buscar
            </Button>
          </form>
        </CardHeader>
        <CardContent className="space-y-3">
          {error ? (
            <Alert title={historyQuery.data ? "Aviso" : "Error"}>
              {historyQuery.data ? error : "No se encontró el serial en este tenant."}
            </Alert>
          ) : null}
          {submitted === "" ? (
            <p className="text-sm text-muted-foreground">
              Ingrese un serial para consultar su historial técnico en compras.
            </p>
          ) : null}
        </CardContent>
      </Card>

      {history ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Despachos</CardTitle>
              <CardDescription>
                Envíos del serial a proveedores y su custodia ({history.serial}).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  { key: "date", header: "Fecha", render: (row) => row.dispatch_date },
                  { key: "supplier", header: "Proveedor", render: (row) => row.supplier_id.slice(0, 8) },
                  {
                    key: "order",
                    header: "Orden",
                    render: (row) => (row.order_id ? row.order_id.slice(0, 8) : "-"),
                  },
                  { key: "service", header: "Servicio", render: (row) => row.service_type },
                  {
                    key: "status",
                    header: "Custodia",
                    render: (row) => (
                      <Badge className={CUSTODY_BADGE[row.status] ?? ""}>{row.status}</Badge>
                    ),
                  },
                  {
                    key: "returned",
                    header: "Devuelto",
                    render: (row) => (row.returned_at ? row.returned_at.slice(0, 10) : "-"),
                  },
                ]}
                rows={history.dispatches}
                rowKey={(row) => row.dispatch_id}
                emptyMessage="Sin despachos registrados para este serial."
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recepciones</CardTitle>
              <CardDescription>
                Recepciones asociadas a los despachos del serial, con su diferencia comercial.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  { key: "date", header: "Fecha", render: (row) => row.receipt_date },
                  { key: "order", header: "Orden", render: (row) => row.order_id.slice(0, 8) },
                  { key: "accepted", header: "Aceptadas", render: (row) => row.qty_accepted ?? "-" },
                  { key: "rejected", header: "Rechazadas", render: (row) => row.qty_rejected ?? "-" },
                  {
                    key: "difference",
                    header: "Diferencia",
                    render: (row) =>
                      row.difference_type ? (
                        <Badge className={DIFFERENCE_BADGE[row.difference_type] ?? ""}>
                          {row.difference_type}
                        </Badge>
                      ) : (
                        "-"
                      ),
                  },
                ]}
                rows={history.receipts}
                rowKey={(row) => row.receipt_id}
                emptyMessage="Sin recepciones vinculadas a este serial."
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Servicios</CardTitle>
              <CardDescription>
                Servicios realizados por el proveedor, con la vigencia legal de PH/retimbrados resaltada.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  { key: "type", header: "Tipo", render: (row) => row.service_type },
                  {
                    key: "cost",
                    header: "Costo",
                    render: (row) => (row.cost != null ? row.cost : "-"),
                  },
                  { key: "test_date", header: "Fecha prueba", render: (row) => row.test_date ?? "-" },
                  {
                    key: "vigencia",
                    header: "Vigencia",
                    render: (row) => <VigenciaBadge nextTestDate={row.next_test_date} result={row.result} />,
                  },
                  { key: "doc", header: "Ref. documental", render: (row) => row.document_ref ?? "-" },
                  { key: "created", header: "Registrado", render: (row) => row.created_at.slice(0, 10) },
                ]}
                rows={history.services}
                rowKey={(row) => `${row.receipt_id}-${row.created_at}`}
                emptyMessage="Sin servicios registrados para este serial."
              />
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
