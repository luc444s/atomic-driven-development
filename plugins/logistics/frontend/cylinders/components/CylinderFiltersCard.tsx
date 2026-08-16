import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { Checkbox } from "@systutor/shell/ui/checkbox";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { Button } from "@systutor/shell/ui/button";

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
