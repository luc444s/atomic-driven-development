import { FormEvent, useEffect, useMemo, useState } from "react";

import { useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../apps/web/src/shared/ui/card";
import { Combobox } from "../../../../apps/web/src/shared/ui/combobox";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input, Textarea } from "../../../../apps/web/src/shared/ui/input";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import { getProduct, productosKeys } from "../../../productos/frontend/api";
import type { Product, ProductListItem } from "../../../productos/frontend/types";
import { listBalances, stockKeys } from "../../../stock/frontend/api";
import type { StockBalanceItem } from "../../../stock/frontend/types";
import {
  fillCylinder,
  listCylinders,
  logisticsKeys,
  type LogisticsCylinder,
} from "../api";
import {
  buildCryogenicFillPreview,
  buildCryogenicTankSourceCards,
  pickFillableSerialIds,
  resolveActiveCryogenicRecipe,
  type CryogenicTankSourceCard,
} from "./helpers";

const EMPTY_SOURCE_STATES = new Set(["CREADO_VACIO", "EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN"]);
const STOCK_BALANCE_PAGE_LIMIT = 200;

type CryogenicFillResult = {
  fillOperationId: string;
  requestedCount: number;
  executedCount: number;
  filledSerials: string[];
  skippedSerials: string[];
  failedSerials: string[];
  litersConsumed: number;
  projectedBalance: number;
};

interface CryogenicFillingDialogProps {
  open: boolean;
  canFill: boolean;
  products: ProductListItem[];
  onOpenChange: (open: boolean) => void;
}

export function CryogenicFillingDialog({
  open,
  canFill,
  products,
  onOpenChange,
}: CryogenicFillingDialogProps) {
  const queryClient = useQueryClient();
  const [selectedSourceKey, setSelectedSourceKey] = useState("");
  const [selectedResultProductId, setSelectedResultProductId] = useState("");
  const [serialQuery, setSerialQuery] = useState("");
  const [selectedSerialIds, setSelectedSerialIds] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<CryogenicFillResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [productDetailsById, setProductDetailsById] = useState<Record<string, Product>>({});
  const [productDetailsError, setProductDetailsError] = useState<string | null>(null);
  const [isLoadingProductDetails, setIsLoadingProductDetails] = useState(false);

  const cylindersQuery = useQuery({
    queryKey: [...logisticsKeys.cylinders.all(), "cryogenic-fill", "all-active"],
    queryFn: () => listCylinders({ active: true }),
    enabled: open && canFill,
  });
  const balancesQuery = useQuery({
    queryKey: [...stockKeys.balances.all, "cryogenic-fill", "all-positive"],
    queryFn: listAllBalancesForCryogenicFill,
    enabled: open && canFill,
  });

  useEffect(() => {
    if (open) {
      return;
    }
    setSelectedSourceKey("");
    setSelectedResultProductId("");
    setSerialQuery("");
    setSelectedSerialIds([]);
    setNotes("");
    setSubmitError(null);
    setResult(null);
  }, [open]);

  const emptyCylinders = useMemo(
    () =>
      (cylindersQuery.data ?? []).filter(
        (cylinder) =>
          cylinder.product_id !== null &&
          cylinder.warehouse_id !== null &&
          cylinder.fill_status === "VACIO" &&
          EMPTY_SOURCE_STATES.has(cylinder.current_state),
      ),
    [cylindersQuery.data],
  );

  const productListById = useMemo(
    () => new Map(products.map((product) => [product.id, product] as const)),
    [products],
  );

  const candidateResultProductIds = useMemo(
    () => Array.from(new Set(emptyCylinders.map((cylinder) => cylinder.product_id).filter(Boolean))) as string[],
    [emptyCylinders],
  );

  useEffect(() => {
    if (!open || candidateResultProductIds.length === 0) {
      return;
    }

    const missingProductIds = candidateResultProductIds.filter(
      (productId) => productDetailsById[productId] === undefined,
    );
    if (missingProductIds.length === 0) {
      return;
    }

    let isCancelled = false;
    setIsLoadingProductDetails(true);
    setProductDetailsError(null);

    Promise.allSettled(missingProductIds.map((productId) => getProduct(productId)))
      .then((responses) => {
        if (isCancelled) {
          return;
        }

        const nextEntries: Record<string, Product> = {};
        let hasFailures = false;
        responses.forEach((response, index) => {
          if (response.status === "fulfilled") {
            nextEntries[missingProductIds[index]] = response.value;
            return;
          }
          hasFailures = true;
        });

        if (Object.keys(nextEntries).length > 0) {
          setProductDetailsById((current) => ({ ...current, ...nextEntries }));
        }
        if (hasFailures) {
          setProductDetailsError(
            "No se pudieron cargar todas las recetas activas de cilindros resultado.",
          );
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoadingProductDetails(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [candidateResultProductIds, open, productDetailsById]);

  const recipeByResultProductId = useMemo(() => {
    const map = new Map<string, NonNullable<ReturnType<typeof resolveActiveCryogenicRecipe>>>();
    candidateResultProductIds.forEach((productId) => {
      const recipe = resolveActiveCryogenicRecipe(productDetailsById[productId]);
      if (recipe) {
        map.set(productId, recipe);
      }
    });
    return map;
  }, [candidateResultProductIds, productDetailsById]);

  const cryoTanks = useMemo(
    () =>
      (cylindersQuery.data ?? []).filter(
        (cylinder) => cylinder.container_type === "CRYOGENIC_TANK" && cylinder.is_active,
      ),
    [cylindersQuery.data],
  );

  const sourceCards: CryogenicTankSourceCard[] = useMemo(
    () =>
      buildCryogenicTankSourceCards({
        tanks: cryoTanks,
        balances: balancesQuery.data ?? [],
        emptyResultCylinders: emptyCylinders,
        recipeByResultProductId,
        productsById: productListById,
      }),
    [cryoTanks, balancesQuery.data, emptyCylinders, productListById, recipeByResultProductId],
  );

  const selectedSource = useMemo(
    () => sourceCards.find((card) => card.key === selectedSourceKey) ?? null,
    [selectedSourceKey, sourceCards],
  );

  const resultProductOptions = useMemo(() => {
    if (!selectedSource) {
      return [];
    }

    return selectedSource.resultProductIds
      .map((productId) => {
        const recipe = recipeByResultProductId.get(productId);
        if (!recipe || recipe.source_product_id !== selectedSource.sourceProductId) {
          return null;
        }
        const product = productListById.get(productId);
        const eligibleCount = emptyCylinders.filter(
          (cylinder) =>
            cylinder.product_id === productId && cylinder.warehouse_id === selectedSource.warehouseId,
        ).length;
        if (eligibleCount === 0) {
          return null;
        }
        return {
          value: productId,
          label: `${product?.sku ?? productId} · ${product?.name ?? productId} (${eligibleCount} vacíos)`,
          keywords: [product?.sku ?? "", product?.name ?? ""],
        };
      })
      .filter((item): item is { value: string; label: string; keywords: string[] } => item !== null)
      .sort((left, right) => left.label.localeCompare(right.label));
  }, [emptyCylinders, productListById, recipeByResultProductId, selectedSource]);

  const selectedRecipe = useMemo(
    () => recipeByResultProductId.get(selectedResultProductId) ?? null,
    [recipeByResultProductId, selectedResultProductId],
  );
  const selectedResultProduct = useMemo(
    () => productListById.get(selectedResultProductId) ?? null,
    [productListById, selectedResultProductId],
  );

  const eligibleCylinders = useMemo(() => {
    if (!selectedSource || !selectedResultProductId) {
      return [];
    }
    return emptyCylinders.filter(
      (cylinder) =>
        cylinder.product_id === selectedResultProductId &&
        cylinder.warehouse_id === selectedSource.warehouseId,
    );
  }, [emptyCylinders, selectedResultProductId, selectedSource]);

  const filteredEligibleCylinders = useMemo(() => {
    const normalizedQuery = serialQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return eligibleCylinders;
    }
    return eligibleCylinders.filter((cylinder) => {
      const barcode = cylinder.barcode2 ?? cylinder.barcode1 ?? "";
      return (
        cylinder.serial.toLowerCase().includes(normalizedQuery) ||
        barcode.toLowerCase().includes(normalizedQuery)
      );
    });
  }, [eligibleCylinders, serialQuery]);

  const selectedCylinderMap = useMemo(
    () => new Map(eligibleCylinders.map((cylinder) => [cylinder.id, cylinder] as const)),
    [eligibleCylinders],
  );
  const selectedCylinders = useMemo(
    () => selectedSerialIds.map((serialId) => selectedCylinderMap.get(serialId)).filter(Boolean) as LogisticsCylinder[],
    [selectedCylinderMap, selectedSerialIds],
  );

  const preview = useMemo(
    () =>
      buildCryogenicFillPreview({
        selectedCount: selectedSerialIds.length,
        litersPerCylinder: selectedRecipe?.source_quantity_liters ?? null,
        litersAvailable: selectedSource?.availableLiters ?? null,
      }),
    [selectedRecipe?.source_quantity_liters, selectedSerialIds.length, selectedSource?.availableLiters],
  );

  const validationError = useMemo(() => {
    if (!canFill) {
      return "No tienes permiso para registrar llenados desde esta vista.";
    }
    if (!selectedSource) {
      return "Selecciona un tanque criogénico para iniciar la corrida.";
    }
    if (!selectedResultProductId) {
      return "Selecciona el tipo de cilindro resultado.";
    }
    if (!selectedRecipe) {
      return "El tipo elegido no tiene receta vigente asociada.";
    }
    if (selectedSerialIds.length === 0) {
      return "Selecciona al menos un serial vacío del tipo correcto.";
    }
    if (preview.fillableCount === 0) {
      return "El stock fuente actual no alcanza para llenar ningún serial seleccionado.";
    }
    return null;
  }, [canFill, preview.fillableCount, selectedRecipe, selectedResultProductId, selectedSerialIds.length, selectedSource]);

  const cylindersWithoutHydrotest = useMemo(
    () => selectedCylinders.filter((cylinder) => !hasValidHydrotest(cylinder)),
    [selectedCylinders],
  );

  useEffect(() => {
    setSelectedResultProductId("");
    setSelectedSerialIds([]);
    setSerialQuery("");
    setNotes("");
    setSubmitError(null);
    setResult(null);
  }, [selectedSourceKey]);

  useEffect(() => {
    setSelectedSerialIds([]);
    setSerialQuery("");
    setSubmitError(null);
    setResult(null);
  }, [selectedResultProductId]);

  function toggleSerialSelection(cylinderId: string) {
    setSelectedSerialIds((current) =>
      current.includes(cylinderId)
        ? current.filter((item) => item !== cylinderId)
        : [...current, cylinderId],
    );
  }

  function addVisibleSerials() {
    setSelectedSerialIds((current) => {
      const next = new Set(current);
      filteredEligibleCylinders.forEach((cylinder) => {
        next.add(cylinder.id);
      });
      return Array.from(next);
    });
  }

  function adjustSelectionToAvailable() {
    setSelectedSerialIds((current) => pickFillableSerialIds(current, preview.fillableCount));
  }

  function addExactSerialMatch() {
    const normalizedQuery = serialQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return;
    }
    const exactMatch = eligibleCylinders.find(
      (cylinder) =>
        cylinder.serial.toLowerCase() === normalizedQuery ||
        (cylinder.barcode2 ?? cylinder.barcode1 ?? "").toLowerCase() === normalizedQuery,
    );
    if (!exactMatch) {
      setSubmitError("No se encontró un serial vacío elegible con ese código.");
      return;
    }
    setSubmitError(null);
    setSelectedSerialIds((current) =>
      current.includes(exactMatch.id) ? current : [...current, exactMatch.id],
    );
    setSerialQuery("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedSource || !selectedRecipe || validationError) {
      setSubmitError(validationError);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setResult(null);

    const fillOperationId = buildFillOperationId();
    const targetSerialIds = preview.isPartial
      ? pickFillableSerialIds(selectedSerialIds, preview.fillableCount)
      : selectedSerialIds;
    const targetCylinders = targetSerialIds
      .map((serialId) => selectedCylinderMap.get(serialId))
      .filter(Boolean) as LogisticsCylinder[];
    const skippedSerials = preview.isPartial
      ? selectedSerialIds
          .slice(targetSerialIds.length)
          .map((serialId) => selectedCylinderMap.get(serialId)?.serial ?? serialId)
      : [];
    const filledSerials: string[] = [];
    const failedSerials: string[] = [];

    for (const cylinder of targetCylinders) {
      try {
        await fillCylinder(cylinder.id, {
          warehouse_id: selectedSource.warehouseId,
          source_product_id: selectedSource.sourceProductId,
          source_cylinder_id: selectedSource.tankId,
          fill_operation_id: fillOperationId,
          notes: notes.trim() || null,
        });
        filledSerials.push(cylinder.serial);
      } catch (error) {
        failedSerials.push(cylinder.serial);
      }
    }

    const litersConsumed = filledSerials.length * (selectedRecipe.source_quantity_liters ?? 0);
    const projectedBalance = (selectedSource.availableLiters ?? 0) - litersConsumed;
    const executedCount = filledSerials.length;
    const notFilledSerials = [...skippedSerials, ...failedSerials];

    setResult({
      fillOperationId,
      requestedCount: selectedSerialIds.length,
      executedCount,
      filledSerials,
      skippedSerials,
      failedSerials,
      litersConsumed,
      projectedBalance,
    });

    if (executedCount > 0) {
      toast.success("Corrida de llenado registrada");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
        queryClient.invalidateQueries({ queryKey: stockKeys.balances.all }),
        queryClient.invalidateQueries({ queryKey: stockKeys.ledger.all({}) }),
        queryClient.invalidateQueries({ queryKey: productosKeys.products.all }),
      ]);
      setSelectedSerialIds((current) => current.filter((serialId) => !targetSerialIds.includes(serialId)));
    }

    if (executedCount === 0) {
      setSubmitError(
        "No se pudo completar ningún llenado. Revisa la disponibilidad de stock o el estado actual de los seriales.",
      );
    } else if (notFilledSerials.length > 0) {
      setSubmitError(
        "La corrida terminó con llenado parcial. Revisa los seriales no completados antes de cerrar.",
      );
    }

    setIsSubmitting(false);
  }

  const isBusy = cylindersQuery.isLoading || balancesQuery.isLoading || isLoadingProductDetails;
  const queryError =
    (cylindersQuery.error instanceof Error && cylindersQuery.error.message) ||
    (balancesQuery.error instanceof Error && balancesQuery.error.message) ||
    productDetailsError;

  return (
    <Dialog
      open={open}
      title="Planta de llenado criogénico"
      description="Elige un tanque criogénico real, selecciona seriales vacíos del mismo tipo y confirma la corrida con preview visible de litros."
      maxWidthClassName="max-w-6xl"
      onClose={() => onOpenChange(false)}
    >
      {!canFill ? (
        <Alert title="Operación no permitida">
          Tu usuario no tiene permiso `logistics.cylinder.update` para ejecutar llenados desde Envases.
        </Alert>
      ) : queryError ? (
        <Alert title="No se pudo cargar la planta de llenado">{queryError}</Alert>
      ) : isBusy ? (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Cargando tanques criogénicos, recetas y seriales elegibles...</p>
        </div>
      ) : !selectedSource ? (
        <div className="space-y-6">
          <p className="text-sm text-muted-foreground">
            Selecciona el tanque criogénico real desde el que saldrá el contenido. Cada card muestra el gas líquido, los litros disponibles desde el balance de stock y los seriales vacíos compatibles.
          </p>
          {sourceCards.length === 0 ? (
            <Alert title="Sin tanques disponibles">
              No hay tanques criogénicos registrados con gas líquido y seriales vacíos compatibles en este momento.
            </Alert>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {sourceCards.map((card) => (
                <Card key={card.key}>
                  <CardHeader>
                    <CardTitle>{card.description || card.serial}</CardTitle>
                    <CardDescription>{card.serial} · {card.sourceProductSku}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-1 text-sm text-foreground">
                      <p>Gas líquido: {card.sourceProductName}</p>
                      <p>Almacén: {card.warehouseName || "-"}</p>
                      <p>Litros disponibles: {formatLiters(card.availableLiters)} L</p>
                      <p>Capacidad nominal: {card.nominalCapacityM3 !== null ? `${formatMetric(card.nominalCapacityM3)} m3` : "-"}</p>
                      <p>Estado: {card.availableLiters > 0 ? "Con carga" : "Vacio"}</p>
                      <p>Seriales vacíos elegibles: {card.eligibleEmptyCount}</p>
                    </div>
                    <div className="flex justify-end gap-3">
                      <Button
                        type="button"
                        disabled={card.eligibleEmptyCount === 0}
                        onClick={() => setSelectedSourceKey(card.key)}
                      >
                        Iniciar llenado
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : (
        <form className="space-y-6" onSubmit={handleSubmit}>
          {submitError ? <Alert title="Corrida no completada">{submitError}</Alert> : null}

          <div className="rounded-md border border-border p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-1">
                <p className="text-lg font-semibold text-foreground">{selectedSource.description || selectedSource.serial}</p>
                <p className="text-sm text-muted-foreground">
                  Tanque {selectedSource.serial} · {selectedSource.sourceProductSku}
                </p>
                <p className="text-sm text-foreground">Gas líquido: {selectedSource.sourceProductName}</p>
                <p className="text-sm text-foreground">Almacén: {selectedSource.warehouseName || "-"}</p>
                <p className="text-sm text-foreground">Disponible: {formatLiters(selectedSource.availableLiters)} L</p>
                <p className="text-sm text-foreground">Estado: {selectedSource.availableLiters > 0 ? "Con carga" : "Vacio"}</p>
              </div>
              <div className="flex gap-3">
                <Button type="button" variant="secondary" onClick={() => setSelectedSourceKey("")}>Cambiar tanque</Button>
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
            <div className="space-y-6">
              <div className="rounded-md border border-border p-4 space-y-4">
                <p className="text-sm font-medium text-foreground">Tipo de cilindro resultado</p>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Producto resultado</span>
                  <Combobox
                    value={selectedResultProductId}
                    onChange={setSelectedResultProductId}
                    options={resultProductOptions}
                    placeholder="Seleccionar tipo de cilindro"
                    searchPlaceholder="Buscar tipo..."
                    emptyMessage="Sin tipos compatibles para esta fuente."
                  />
                </label>
                {selectedRecipe && selectedResultProduct ? (
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-md border border-border p-3 text-sm text-foreground">
                      <p className="font-medium">Litros por cilindro</p>
                      <p>{formatLiters(selectedRecipe.source_quantity_liters ?? 0)} L</p>
                    </div>
                    <div className="rounded-md border border-border p-3 text-sm text-foreground">
                      <p className="font-medium">Resultado m3 gas</p>
                      <p>{formatMetric(selectedRecipe.net_volume_m3)}</p>
                    </div>
                    <div className="rounded-md border border-border p-3 text-sm text-foreground">
                      <p className="font-medium">Resultado peso neto</p>
                      <p>{formatMetric(selectedRecipe.net_weight_kg)} kg</p>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="rounded-md border border-border p-4 space-y-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                  <label className="block space-y-2 text-sm text-foreground lg:max-w-sm lg:flex-1">
                    <span>Buscar o escanear serial</span>
                    <Input
                      value={serialQuery}
                      onChange={(event) => setSerialQuery(event.target.value)}
                      placeholder="Serial o barcode"
                    />
                  </label>
                  <div className="flex gap-3">
                    <Button type="button" variant="secondary" onClick={addExactSerialMatch}>
                      Agregar serial buscado
                    </Button>
                    <Button type="button" variant="secondary" onClick={addVisibleSerials}>
                      Seleccionar lote
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => setSelectedSerialIds([])}>
                      Limpiar selección
                    </Button>
                  </div>
                </div>

                <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-foreground">Seriales vacíos elegibles</p>
                    <div className="max-h-96 space-y-2 overflow-y-auto rounded-md border border-border p-3">
                      {filteredEligibleCylinders.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No hay seriales vacíos visibles para el tipo seleccionado.
                        </p>
                      ) : (
                        filteredEligibleCylinders.map((cylinder) => {
                          const isSelected = selectedSerialIds.includes(cylinder.id);
                          return (
                            <div
                              key={cylinder.id}
                              className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2"
                            >
                              <div className="space-y-1 text-sm text-foreground">
                                <p className="font-medium">{cylinder.serial}</p>
                                <p className="text-xs text-muted-foreground">
                                  {cylinder.location_context || cylinder.warehouse_name || "En almacén"}
                                </p>
                                {!hasValidHydrotest(cylinder) ? (
                                  <p className="text-xs text-destructive">Sin PH vigente</p>
                                ) : null}
                              </div>
                              <Button
                                type="button"
                                variant="secondary"
                                onClick={() => toggleSerialSelection(cylinder.id)}
                              >
                                {isSelected ? "Quitar" : "Agregar"}
                              </Button>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <p className="text-sm font-medium text-foreground">Seriales seleccionados</p>
                    <div className="max-h-96 space-y-2 overflow-y-auto rounded-md border border-border p-3">
                      {selectedCylinders.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Aún no has seleccionado seriales para esta corrida.
                        </p>
                      ) : (
                        selectedCylinders.map((cylinder, index) => (
                          <div
                            key={cylinder.id}
                            className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2"
                          >
                            <div className="space-y-1 text-sm text-foreground">
                              <p className="font-medium">{index + 1}. {cylinder.serial}</p>
                              <p className="text-xs text-muted-foreground">
                                {cylinder.warehouse_name || cylinder.location_context || "Sin contexto"}
                              </p>
                              {!hasValidHydrotest(cylinder) ? (
                                <p className="text-xs text-destructive">Sin PH vigente</p>
                              ) : null}
                            </div>
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => toggleSerialSelection(cylinder.id)}
                            >
                              Quitar
                            </Button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {cylindersWithoutHydrotest.length > 0 ? (
                <Alert title="Prueba hidrostática faltante o vencida">
                  Los siguientes seriales no tienen prueba hidrostática vigente y el llenado fallará:{" "}
                  <strong>{cylindersWithoutHydrotest.map((c) => c.serial).join(", ")}</strong>
                  . Debes registrar una prueba hidrostática antes de intentar llenarlos.
                </Alert>
              ) : null}

              <div className="rounded-md border border-border p-4 space-y-4">
                <p className="text-sm font-medium text-foreground">Notas de la corrida</p>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Observación operativa</span>
                  <Textarea
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    rows={3}
                    placeholder="Observación opcional para la corrida de planta"
                  />
                </label>
              </div>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Preview de llenado</CardTitle>
                  <CardDescription>
                    Revisa litros requeridos, stock disponible y el impacto total o parcial antes de ejecutar.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-foreground">
                  <p>Criogénico: {selectedSource.sourceProductName}</p>
                  <p>Tipo: {selectedResultProduct?.name ?? "-"}</p>
                  <p>Solicitados: {preview.selectedCount} seriales</p>
                  <p>Litros por cilindro: {selectedRecipe ? `${formatLiters(selectedRecipe.source_quantity_liters ?? 0)} L` : "-"}</p>
                  <p>Litros requeridos: {formatLiters(preview.litersRequired)} L</p>
                  <p>Litros disponibles: {formatLiters(preview.litersAvailable)} L</p>
                  <p>Stock fuente suficiente para: {preview.fillableCount} seriales</p>
                  <p>Saldo proyectado: {formatLiters(preview.projectedBalance)} L</p>
                  <p>Resultado esperado: {preview.isPartial ? "PARCIAL" : preview.selectedCount > 0 ? "TOTAL" : "-"}</p>
                  {preview.isPartial ? (
                    <Alert title="Parcial visible">
                      Solicitaste {preview.selectedCount} seriales, pero el stock fuente sólo alcanza para {preview.fillableCount}. Puedes ajustar la selección o confirmar el parcial de forma explícita.
                    </Alert>
                  ) : null}
                </CardContent>
              </Card>

              {result ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Resultado de la corrida</CardTitle>
                    <CardDescription>
                      La correlación visible queda registrada para auditar el lote ejecutado.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-foreground">
                    <p>fill_operation_id: {result.fillOperationId}</p>
                    <p>Cantidad solicitada: {result.requestedCount}</p>
                    <p>Cantidad llenada real: {result.executedCount}</p>
                    <p>Litros descontados reales: {formatLiters(result.litersConsumed)} L</p>
                    <p>Saldo final proyectado: {formatLiters(result.projectedBalance)} L</p>
                    <p>Seriales llenados: {result.filledSerials.length > 0 ? result.filledSerials.join(", ") : "-"}</p>
                    <p>
                      Seriales no llenados: {result.skippedSerials.length + result.failedSerials.length > 0
                        ? [...result.skippedSerials, ...result.failedSerials].join(", ")
                        : "-"}
                    </p>
                  </CardContent>
                </Card>
              ) : null}

              <div className="flex justify-end gap-3">
                {preview.isPartial && preview.fillableCount > 0 ? (
                  <Button type="button" variant="secondary" onClick={adjustSelectionToAvailable}>
                    Ajustar selección
                  </Button>
                ) : null}
                <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={isSubmitting || validationError !== null}>
                  {preview.isPartial ? "Confirmar parcial" : "Confirmar llenado"}
                </Button>
              </div>
            </div>
          </div>
        </form>
      )}
    </Dialog>
  );
}

function buildFillOperationId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `fill-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

function formatLiters(value: number) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(value);
}

function formatMetric(value: number | null) {
  if (value === null) {
    return "-";
  }
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 3,
  }).format(value);
}

function hasValidHydrotest(cylinder: LogisticsCylinder): boolean {
  if (!cylinder.next_hydrotest_date) {
    return false;
  }
  return new Date(cylinder.next_hydrotest_date) >= new Date(new Date().toDateString());
}

async function listAllBalancesForCryogenicFill(): Promise<StockBalanceItem[]> {
  const collected: StockBalanceItem[] = [];
  let offset = 0;
  let total = Number.POSITIVE_INFINITY;

  while (offset < total) {
    const page = await listBalances({ limit: STOCK_BALANCE_PAGE_LIMIT, offset });
    collected.push(...page.items);
    total = page.total;
    if (page.items.length === 0) {
      break;
    }
    offset += page.limit;
  }

  return collected;
}
