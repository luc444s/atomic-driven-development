import { useState } from "react";

import { type RouteIncident } from "../../api";
import { type SerialSelectionItem } from "./LoadSerialsDialog";
import {
  type RouteContextType,
  type RouteDraftItem,
} from "./RouteOperationForm";
import { suggestCorrectionOperationType } from "./session-route-tab-view";

type ProductSelection = {
  id: string;
  sku: string;
  name: string;
};

export function useSessionRouteTabUiState() {
  const [operationType, setOperationType] = useState("DELIVERY");
  const [routeStopId, setRouteStopId] = useState("");
  const [contextType, setContextType] = useState<RouteContextType>("CUSTOMER");
  const [contextCustomerId, setContextCustomerId] = useState("");
  const [contextWarehouseId, setContextWarehouseId] = useState("");
  const [operationNotes, setOperationNotes] = useState("");
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [nextDirection, setNextDirection] = useState<"OUT" | "IN">("OUT");
  const [draftItems, setDraftItems] = useState<RouteDraftItem[]>([]);
  const [serialItemIndex, setSerialItemIndex] = useState<number | null>(null);
  const [fastSerialInput, setFastSerialInput] = useState("");
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [incidentsModalOpen, setIncidentsModalOpen] = useState(false);
  const [stopResultsModalOpen, setStopResultsModalOpen] = useState(false);
  const [operationsModalOpen, setOperationsModalOpen] = useState(false);
  const [stopProgressModalOpen, setStopProgressModalOpen] = useState(false);
  const [compositionModalOpen, setCompositionModalOpen] = useState(false);
  const [incidentStopId, setIncidentStopId] = useState("");
  const [incidentRelatedOperationId, setIncidentRelatedOperationId] = useState("");
  const [incidentType, setIncidentType] = useState("QUANTITY_MISMATCH");
  const [incidentNotes, setIncidentNotes] = useState("");
  const [resolveIncidentId, setResolveIncidentId] = useState<string | null>(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [correctionIncidentId, setCorrectionIncidentId] = useState<string | null>(null);

  const serialItem = serialItemIndex !== null ? draftItems[serialItemIndex] ?? null : null;
  const serialDialogItem: SerialSelectionItem | null = serialItem
    ? {
        product_id: serialItem.product_id,
        product_name: serialItem.product_name,
        planned_quantity: serialItem.quantity,
        source_warehouse_id: null,
      }
    : null;

  function addDraftProduct(product: ProductSelection) {
    setDraftItems((current) => [
      ...current,
      {
        product_id: product.id,
        product_name: `${product.sku} · ${product.name}`,
        quantity: "1",
        direction: operationType === "DELIVERY" ? "OUT" : operationType === "PICKUP" ? "IN" : nextDirection,
        selected_serials_count: 0,
      },
    ]);
  }

  function addDeliveryProduct(product: { product_id: string; product_name: string; available: number; serial?: string }) {
    setDraftItems((current) => {
      const existingIndex = current.findIndex((item) => item.product_id === product.product_id && item.direction === "OUT");
      if (existingIndex !== -1) {
        return current.map((item, index) =>
          index === existingIndex
            ? {
                ...item,
                quantity: String(Math.min(Number(item.quantity) + 1, product.available)),
                selected_serials_count: product.serial ? item.selected_serials_count + 1 : item.selected_serials_count,
              }
            : item
        );
      }
      return [
        ...current,
        {
          product_id: product.product_id,
          product_name: product.product_name,
          quantity: "1",
          direction: "OUT",
          selected_serials_count: product.serial ? 1 : 0,
        },
      ];
    });
  }

  function updateDraftItem(index: number, patch: Partial<RouteDraftItem>) {
    setDraftItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }

  function removeDraftItem(index: number) {
    setDraftItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function handleRouteStopChange(value: string) {
    setRouteStopId(value);
    if (value) {
      setContextType("STOP");
      setContextCustomerId("");
      setContextWarehouseId("");
      return;
    }
    if (contextType === "STOP") {
      setContextType("CUSTOMER");
    }
  }

  function handleContextTypeChange(value: RouteContextType) {
    setContextType(value);
    if (value !== "CUSTOMER") {
      setContextCustomerId("");
    }
    if (value !== "WAREHOUSE") {
      setContextWarehouseId("");
    }
  }

  function handleOpenProductSearch(direction?: "OUT" | "IN") {
    if (direction) {
      setNextDirection(direction);
    }
    setShowProductSearch(true);
  }

  function openEventModal(defaultStopId?: string) {
    setCorrectionIncidentId(null);
    setEventModalOpen(true);
    if (defaultStopId) {
      setRouteStopId(defaultStopId);
      setContextType("STOP");
      setContextCustomerId("");
      setContextWarehouseId("");
    }
  }

  function closeEventModal() {
    setEventModalOpen(false);
    if (!correctionIncidentId) {
      return;
    }
    cancelCorrection();
  }

  function openIncidentsModal() {
    setIncidentsModalOpen(true);
  }

  function closeIncidentsModal() {
    setIncidentsModalOpen(false);
    setResolveIncidentId(null);
    setResolveNotes("");
  }

  function openStopResultsModal() {
    setStopResultsModalOpen(true);
  }

  function closeStopResultsModal() {
    setStopResultsModalOpen(false);
  }

  function openOperationsModal() {
    setOperationsModalOpen(true);
  }

  function closeOperationsModal() {
    setOperationsModalOpen(false);
  }

  function openStopProgressModal() {
    setStopProgressModalOpen(true);
  }

  function closeStopProgressModal() {
    setStopProgressModalOpen(false);
  }

  function openCompositionModal() {
    setCompositionModalOpen(true);
  }

  function closeCompositionModal() {
    setCompositionModalOpen(false);
  }

  function startResolveIncident(incidentId: string) {
    setCorrectionIncidentId(null);
    setResolveIncidentId(incidentId);
    setResolveNotes("");
  }

  function cancelResolveIncident() {
    setResolveIncidentId(null);
    setResolveNotes("");
  }

  function startCorrection(incident: RouteIncident) {
    setResolveIncidentId(null);
    setResolveNotes("");
    setCorrectionIncidentId(incident.id);
    setOperationType(suggestCorrectionOperationType(incident));
    setRouteStopId(incident.route_stop_id ?? "");
    setContextType(incident.route_stop_id ? "STOP" : "CUSTOMER");
    setOperationNotes(`Reconciliación de incidencia ${incident.id}`);
    setDraftItems([]);
    setIncidentsModalOpen(false);
    setEventModalOpen(true);
  }

  function cancelCorrection() {
    setCorrectionIncidentId(null);
    setDraftItems([]);
    setOperationNotes("");
    setEventModalOpen(false);
  }

  function handleProductSelected(product: ProductSelection) {
    addDraftProduct(product);
    setShowProductSearch(false);
  }

  function closeSerialDialog() {
    setSerialItemIndex(null);
  }

  function resetFastSerialInput() {
    setFastSerialInput("");
  }

  function handleSerialSelectionCountChange(selectedCount: number) {
    if (serialItemIndex === null) {
      return;
    }
    setDraftItems((current) =>
      current.map((item, index) =>
        index === serialItemIndex
          ? {
              ...item,
              quantity: String(selectedCount || 0),
              selected_serials_count: selectedCount,
            }
          : item
      )
    );
  }

  function resetAfterRouteEventSuccess() {
    setOperationNotes("");
    setDraftItems([]);
    setContextCustomerId("");
    setContextWarehouseId("");
    setCorrectionIncidentId(null);
    setEventModalOpen(false);
  }

  function resetAfterIncidentResolved() {
    setResolveIncidentId(null);
    setResolveNotes("");
  }

  function resetAfterIncidentCreated() {
    setIncidentNotes("");
    setIncidentRelatedOperationId("");
  }

  return {
    operationType,
    routeStopId,
    contextType,
    contextCustomerId,
    contextWarehouseId,
    operationNotes,
    showProductSearch,
    draftItems,
    serialDialogItem,
    fastSerialInput,
    eventModalOpen,
    incidentsModalOpen,
    stopResultsModalOpen,
    operationsModalOpen,
    stopProgressModalOpen,
    compositionModalOpen,
    incidentStopId,
    incidentRelatedOperationId,
    incidentType,
    incidentNotes,
    resolveIncidentId,
    resolveNotes,
    correctionIncidentId,
    setOperationType,
    setContextCustomerId,
    setContextWarehouseId,
    setOperationNotes,
    setSerialItemIndex,
    setIncidentStopId,
    setIncidentRelatedOperationId,
    setIncidentType,
    setIncidentNotes,
    setResolveNotes,
    setShowProductSearch,
    setFastSerialInput,
    updateDraftItem,
    removeDraftItem,
    handleRouteStopChange,
    handleContextTypeChange,
    handleOpenProductSearch,
    openEventModal,
    closeEventModal,
    openIncidentsModal,
    closeIncidentsModal,
    openStopResultsModal,
    closeStopResultsModal,
    openOperationsModal,
    closeOperationsModal,
    openStopProgressModal,
    closeStopProgressModal,
    openCompositionModal,
    closeCompositionModal,
    startResolveIncident,
    cancelResolveIncident,
    startCorrection,
    cancelCorrection,
    handleProductSelected,
    addDeliveryProduct,
    closeSerialDialog,
    resetFastSerialInput,
    handleSerialSelectionCountChange,
    resetAfterRouteEventSuccess,
    resetAfterIncidentResolved,
    resetAfterIncidentCreated,
  };
}
