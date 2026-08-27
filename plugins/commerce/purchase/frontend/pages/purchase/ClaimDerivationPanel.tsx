import { useMutation, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { useState } from "react";
import { deriveClaims } from "../../api";
import type { ClaimDerivationResult } from "../../types";
import { Button } from "@systutor/shell/ui/button";
import { Badge } from "@systutor/shell/ui/badge";

const DERIVED_REASON_LABEL: Record<string, string> = {
  FALTANTE: "Faltante",
  PRECIO_INCORRECTO: "Precio incorrecto",
};

type ClaimDerivationPanelProps = {
  orderId: string | null;
  setError: (value: string | null) => void;
};

export function ClaimDerivationPanel({ orderId, setError }: ClaimDerivationPanelProps) {
  const queryClient = useQueryClient();
  const [result, setResult] = useState<ClaimDerivationResult | null>(null);

  const deriveMut = useMutation({
    mutationFn: () => (orderId ? deriveClaims(orderId) : Promise.reject("No order")),
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ["compras", "claims"] });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al derivar reclamaciones"),
  });

  return (
    <div className="space-y-2 border-t border-border pt-3">
      <span className="text-sm text-foreground">Derivar reclamaciones</span>
      <div className="flex items-center gap-2">
        <Button variant="secondary" disabled={!orderId || deriveMut.isPending} onClick={() => deriveMut.mutate()}>
          {deriveMut.isPending ? "Derivando..." : "Derivar reclamaciones"}
        </Button>
        {result ? (
          <span className="text-xs text-muted-foreground">Creadas {result.created.length} · Omitidas {result.skipped}</span>
        ) : null}
      </div>
      {result ? (
        result.created.length ? (
          <div className="space-y-1">
            {result.created.map((cl) => (
              <div key={cl.id} className="text-xs flex items-center gap-2">
                <Badge>{DERIVED_REASON_LABEL[cl.reason] ?? cl.reason}</Badge>
                <span className="text-muted-foreground">{cl.description}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">Sin reclamaciones nuevas: las diferencias ya tienen reclamación derivada.</p>
        )
      ) : null}
    </div>
  );
}
