import { FormEvent, useState } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent } from "@systutor/shell/ui/card";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Alert } from "@systutor/shell/ui/alert";
import { apiRequest } from "@systutor/shell/api/client";

type GenerateCylinderBatchDialogProps = {
  open: boolean;
  onClose: () => void;
  onGenerate: (serials: string[], productId: string) => void;
  gasOptions: Array<{ id: string; name: string }>;
};

function listStockBalances(params: Record<string, unknown>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return apiRequest<{ items: Array<{ product_id: string; product_name: string; warehouse_name: string; quantity: number }>; total: number }>(
    `/api/v1/plugins/stock/balances${qs ? `?${qs}` : ""}`
  );
}

export function GenerateCylinderBatchDialog({
  open,
  onClose,
  onGenerate,
  gasOptions,
}: GenerateCylinderBatchDialogProps) {
  const [prefix, setPrefix] = useState("");
  const [suffixStart, setSuffixStart] = useState("00001");
  const [count, setCount] = useState("100");
  const [productId, setProductId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const stockQuery = useQuery({
    queryKey: ["stock", "balances", "preview", productId],
    queryFn: () => listStockBalances({ product_id: productId, limit: 100 }),
    enabled: Boolean(productId),
  });

  const stockTotal = stockQuery.data?.items?.reduce((sum, item) => sum + (item.quantity ?? 0), 0) ?? null;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!productId) {
      setError("Selecciona un producto.");
      return;
    }

    const padLen = suffixStart.length;
    const startNum = parseInt(suffixStart, 10);
    const total = parseInt(count, 10);

    if (isNaN(startNum) || isNaN(total) || total < 1 || total > 10000) {
      setError("Cantidad invalida (1-10000) o sufijo no numerico.");
      return;
    }

    const serials: string[] = [];
    for (let i = 0; i < total; i++) {
      const num = startNum + i;
      const padded = String(num).padStart(padLen, "0");
      serials.push(`${prefix}${padded}`);
    }

    onGenerate(serials, productId);
    setPrefix("");
    setSuffixStart("00001");
    setCount("100");
    setProductId("");
    setError(null);
  }

  function handleClose() {
    setError(null);
    onClose();
  }

  const productOptions = gasOptions.map((g) => ({ value: g.id, label: g.name }));

  return (
    <Dialog
      open={open}
      title="Generar lote de envases"
      description="Genera seriales en lote con prefijo y sufijo numerico autoincremental."
      onClose={handleClose}
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Producto</span>
          <Combobox
            value={productId}
            onChange={setProductId}
            options={productOptions}
            placeholder="Seleccionar producto"
            searchPlaceholder="Buscar producto"
          />
        </label>

        {stockTotal !== null ? (
          <Card>
            <CardContent className="py-3 text-sm">
              <span className="text-muted-foreground">Stock disponible: </span>
              <span className="font-medium text-foreground">{stockTotal} unidades</span>
            </CardContent>
          </Card>
        ) : null}

        <label className="block space-y-2 text-sm text-foreground">
          <span>Prefijo</span>
          <Input
            value={prefix}
            onChange={(event) => setPrefix(event.target.value)}
            placeholder="LU"
          />
        </label>

        <label className="block space-y-2 text-sm text-foreground">
          <span>Sufijo inicio</span>
          <Input
            value={suffixStart}
            onChange={(event) => setSuffixStart(event.target.value)}
            placeholder="00001"
          />
        </label>

        <label className="block space-y-2 text-sm text-foreground">
          <span>Cantidad</span>
          <Input
            value={count}
            onChange={(event) => setCount(event.target.value)}
            placeholder="100"
          />
        </label>

        {error ? <Alert title="Error">{error}</Alert> : null}

        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancelar
          </Button>
          <Button type="submit">Generar lote</Button>
        </div>
      </form>
    </Dialog>
  );
}
