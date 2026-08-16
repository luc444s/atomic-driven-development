import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@systutor/shell/api/client";
import { Combobox } from "@systutor/shell/ui/combobox";

interface VehicleItem {
  id: string;
  plate: string;
  description: string | null;
  is_active: boolean;
}

const VEHICLE_KEYS = ["logistics", "vehicles", "catalog"] as const;

export interface VehicleSelectProps {
  value: string;
  onChange: (vehicleId: string, plate: string) => void;
  placeholder?: string;
}

export function VehicleSelect({
  value,
  onChange,
  placeholder = "Seleccionar vehículo...",
}: VehicleSelectProps) {
  const [selectedLabel, setSelectedLabel] = useState("");
  const { data: vehicles = [] } = useQuery({
    queryKey: VEHICLE_KEYS,
    queryFn: () => apiRequest<VehicleItem[]>("/api/v1/plugins/logistics/vehicles"),
    staleTime: 60_000,
  });

  const options = useMemo(
    () =>
      vehicles
        .filter((v) => v.is_active)
        .map((v) => ({
          value: v.id,
          label: `${v.plate}${v.description ? ` (${v.description})` : ""}`,
          keywords: [v.plate, v.description ?? ""],
        })),
    [vehicles],
  );

  return (
    <label className="block space-y-2 text-sm text-foreground">
      <span>Vehículo (opcional)</span>
      <Combobox
        value={value}
        onChange={(id) => {
          const option = options.find((o) => o.value === id);
          const label = option?.label ?? "";
          setSelectedLabel(label);
          onChange(id, label);
        }}
        options={options}
        placeholder={placeholder}
        searchPlaceholder="Buscar vehículo..."
        emptyMessage="Sin vehículos disponibles."
        selectedLabel={selectedLabel}
      />
    </label>
  );
}
