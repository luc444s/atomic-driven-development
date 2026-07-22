// Auto-generado por split-tsx.py
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Select } from "../../../../../apps/web/src/shared/ui/select";

interface TransitionDialogProps {
  isTransitionOpen: boolean;
  setIsTransitionOpen: (open: boolean) => void;
  nextState: string;
  setNextState: (value: string) => void;
  handleTransition: () => void;
  transitionMutation: { isPending: boolean };
  transitionsQuery: { data: Array<{ to_state: string }> };
  getCylinderStateLabel: (state: string) => string;
}

export function TransitionDialog({
    isTransitionOpen,
    setIsTransitionOpen,
    nextState,
    setNextState,
    handleTransition,
    transitionMutation,
    transitionsQuery,
    getCylinderStateLabel,
}: TransitionDialogProps) {
  return (
<Dialog open={isTransitionOpen} title="Corrección de estado" description="Usa esta acción solo para regularización o corrección excepcional. La operación normal debe venir de los flujos operativos reales." onClose={() => setIsTransitionOpen(false)}>
  <div className="space-y-4">
    <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm text-foreground">
      No usar para operación normal. Solo soporte o corrección de datos.
    </div>
    <Select
      value={nextState}
      onChange={(value) => setNextState(value)}
      placeholder="Selecciona estado corregido"
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
        Aplicar corrección
      </Button>
    </div>
  </div>
</Dialog>
  );
}
