import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";

import type { SessionReconciliation } from "../../api";

type Props = {
  reconciliation: SessionReconciliation | undefined;
  counts: Record<string, string>;
  setCounts: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  onSaveCount: () => void;
  isPending: boolean;
  error: string | null;
};

export function SessionReconciliationTab({
  reconciliation,
  counts,
  setCounts,
  onSaveCount,
  isPending,
  error,
}: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Conteo físico</CardTitle>
          <CardDescription>
            Registra el conteo contra el saldo real del almacén móvil.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <DataTable
            columns={[
              { key: "product", header: "Producto", render: (row) => row.product_name },
              {
                key: "expected",
                header: "Esperado",
                render: (row) => String(row.expected_quantity),
              },
              {
                key: "counted",
                header: "Conteo",
                render: (row) => (
                  <Input
                    value={counts[row.product_id] ?? "0"}
                    onChange={(event) =>
                      setCounts((current) => ({ ...current, [row.product_id]: event.target.value }))
                    }
                  />
                ),
              },
              { key: "diff", header: "Dif.", render: (row) => String(row.difference_quantity ?? 0) },
            ]}
            rows={reconciliation?.lines ?? []}
            rowKey={(row) => row.product_id}
            emptyMessage="No hay líneas para conciliar todavía."
          />
          <div className="flex gap-2">
            <Button disabled={isPending} onClick={onSaveCount}>
              Guardar conteo
            </Button>
          </div>
          {error ? <Alert title="Estado no actualizado">{error}</Alert> : null}
        </CardContent>
      </Card>
    </div>
  );
}
