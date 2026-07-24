import { useState } from "react";

export function usePlanningFilters() {
  const [vehicleId, setVehicleId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");

  return {
    vehicleId,
    setVehicleId,
    warehouseId,
    setWarehouseId,
  };
}
