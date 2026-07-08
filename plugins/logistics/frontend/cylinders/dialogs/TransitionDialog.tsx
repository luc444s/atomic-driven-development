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
<Dialog open={isTransitionOpen} title="Transición operativa" description="Aplica la siguiente transición válida del state machine." onClose={() => setIsTransitionOpen(false)}>
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
</Dialog>
  );
}
