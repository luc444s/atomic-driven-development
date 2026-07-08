import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Checkbox } from "../../../../../apps/web/src/shared/ui/checkbox";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Button } from "../../../../../apps/web/src/shared/ui/button";

interface CylinderFiltersCardProps {
  search: string;
  stateFilter: string;
  medicalOnly: boolean;
  stateOptions: Array<{ value: string; label: string }>;
  onSearchChange: (value: string) => void;
  onStateFilterChange: (value: string) => void;
  onMedicalOnlyChange: (checked: boolean) => void;
  onReset: () => void;
}

export function CylinderFiltersCard({
  search,
  stateFilter,
  medicalOnly,
  stateOptions,
  onSearchChange,
  onStateFilterChange,
  onMedicalOnlyChange,
  onReset,
}: CylinderFiltersCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Consulta rápida</CardTitle>
        <CardDescription>Busca por serie, barcode, matrícula o ubicación.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-4">
        <Input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Serie o barcode" />
        <Select
          value={stateFilter}
          onChange={onStateFilterChange}
          placeholder="Todos los estados"
          options={stateOptions}
        />
        <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-foreground">
          <Checkbox checked={medicalOnly} onChange={(event) => onMedicalOnlyChange(event.currentTarget.checked)} />
          Solo medicinales
        </label>
        <Button variant="secondary" onClick={onReset}>
          Limpiar filtros
        </Button>
      </CardContent>
    </Card>
  );
}
