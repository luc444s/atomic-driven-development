import { useState } from "react";

export type CreateReservationDraft = {
  vehicleId: string;
  plannedStartAt: string;
  plannedEndAt: string;
} | null;

export function usePlanningSelection() {
  const [selectedReservationId, setSelectedReservationId] = useState<string | null>(null);
  const [createDraft, setCreateDraft] = useState<CreateReservationDraft>(null);
  const [editingReservationId, setEditingReservationId] = useState<string | null>(null);

  return {
    selectedReservationId,
    setSelectedReservationId,
    createDraft,
    setCreateDraft,
    editingReservationId,
    setEditingReservationId,
  };
}
