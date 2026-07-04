import { FormEvent, useMemo, useRef, useState } from "react";
import type { CustomerBrief } from "../../crm/frontend/types";

import { useMutation, useQuery, useQueryClient } from "../../../apps/web/src/lib/react-query";
import { useAuthStore } from "../../../apps/web/src/features/auth/store";
import { Alert } from "../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../apps/web/src/shared/ui/card";
import { ConfirmDialog } from "../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../apps/web/src/shared/ui/dialog";
import { DropdownMenu, type DropdownItem } from "../../../apps/web/src/shared/ui/dropdown-menu";
import { Input, Textarea } from "../../../apps/web/src/shared/ui/input";
import { Select } from "../../../apps/web/src/shared/ui/select";
import { CustomerSearchDialog } from "../../crm/frontend/components/CustomerSearchDialog";
import { getProduct, listAllProducts, listBrands as listProductBrands, listSubline, productosKeys } from "../../productos/frontend/api";
import { CylinderStateBadge, getCylinderStateLabel } from "./CylinderStateBadge";
import { LogisticsSection } from "./components/LogisticsSection";
import type { CylinderEntryMode } from "./api";
import {
  type LogisticsCylinder,
  createCylinder,
  createCylinderService,
  createHydrotest,
  createRetimbrado,
  createWarranty,
  deleteCylinderService,
  getAllowedTransitions,
  getCylinderLabelData,
  listConditions,
  listCylinderServices,
  listCylinders,
  listCylinderStates,
  listCylinderSummary,
  listCylinderTrace,
  listBrands,
  listGasProducts,
  listHydrotests,
  listLabelHistory,
  listOwnership,
  listRetimbrados,
  listScanLogs,
  listServiceTypes,
  listWarranties,
  logisticsKeys,
  printLabel,
  processScan,
  transitionCylinder,
  updateCylinder,
  updateCylinderService,
} from "./api";
import { CreateCylinderDialog } from "./cylinders/dialogs/create-cylinder-dialog";
import { EditCylinderDialog } from "./cylinders/dialogs/edit-cylinder-dialog";
import { CylinderViewSectionDialog } from "./cylinders/dialogs/cylinder-view-section-dialog";
import {
  type CylinderFormState,
  type CylinderCreateMetaState,
  type HydrotestFormState,
  type WarrantyFormState,
  type RetimbradoFormState,
  type ServiceFormState,
  type PrintLabelFormState,
  type ScanFormState,
  EMPTY_CYLINDER_FORM,
  EMPTY_HYDROTEST_FORM,
  EMPTY_WARRANTY_FORM,
  EMPTY_RETIMBRADO_FORM,
  EMPTY_SERVICE_FORM,
  EMPTY_PRINT_LABEL_FORM,
  EMPTY_SCAN_FORM,
  EMPTY_CYLINDER_CREATE_META,
} from "./cylinders/forms/cylinder-form-state";
import {
  buildCylinderFormState,
  buildCylinderPayload,
  buildCreateCylinderPayload,
} from "./cylinders/forms/cylinder-payload";
import { toNullable, toNumberOrNull, toIntegerOrNull, formatDate, formatDateTime, InfoBlock, DataCard, Field } from "./cylinders/utils/formatters";

export function LogisticsPage() {
  const queryClient = useQueryClient();
  const permissions = useAuthStore((state) => state.permissions);

  const canCreate = permissions.includes("logistics.cylinder.create");
  const canUpdate = permissions.includes("logistics.cylinder.update");
  const canTransition = permissions.includes("logistics.cylinder.transition");
  const canTrace = permissions.includes("logistics.cylinder.trace");
  const canMaintenance = permissions.includes("logistics.maintenance.manage");
  const canRetimbrado = permissions.includes("logistics.retimbrado.manage");
  const canLabelPrint = permissions.includes("logistics.label.print");
  const canServiceManage = permissions.includes("logistics.service.manage");
  const canServiceRead = permissions.includes("logistics.service.read");
  const canScan = permissions.includes("logistics.scan.execute");
  const canScanRead = permissions.includes("logistics.scan.read");
  const canOwnershipRead = permissions.includes("logistics.cylinder.ownership.read");

  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [selectedCylinder, setSelectedCylinder] = useState<LogisticsCylinder | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isHydrotestOpen, setIsHydrotestOpen] = useState(false);
  const [isWarrantyOpen, setIsWarrantyOpen] = useState(false);
  const [isCreateCustomerSearchOpen, setIsCreateCustomerSearchOpen] = useState(false);
  const [isWarrantyCustomerSearchOpen, setIsWarrantyCustomerSearchOpen] = useState(false);
  const [isRetimbradoOpen, setIsRetimbradoOpen] = useState(false);
  const [isServiceOpen, setIsServiceOpen] = useState(false);
  const [isTransitionOpen, setIsTransitionOpen] = useState(false);
  const [isPrintLabelOpen, setIsPrintLabelOpen] = useState(false);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [isDetailMenuOpen, setIsDetailMenuOpen] = useState(false);
  const [isFullDetailOpen, setIsFullDetailOpen] = useState(false);
  const [selectedViewSection, setSelectedViewSection] = useState<"trace" | "ph" | "retimbrados" | "custody" | "services" | "label" | null>(null);
  const [nextState, setNextState] = useState("");
  const [cylinderForm, setCylinderForm] = useState<CylinderFormState>(EMPTY_CYLINDER_FORM);
  const [createMeta, setCreateMeta] = useState<CylinderCreateMetaState>(EMPTY_CYLINDER_CREATE_META);
  const [hydrotestForm, setHydrotestForm] = useState<HydrotestFormState>(EMPTY_HYDROTEST_FORM);
  const [warrantyForm, setWarrantyForm] = useState<WarrantyFormState>(EMPTY_WARRANTY_FORM);
  const [retimbradoForm, setRetimbradoForm] = useState<RetimbradoFormState>(EMPTY_RETIMBRADO_FORM);
  const [serviceForm, setServiceForm] = useState<ServiceFormState>(EMPTY_SERVICE_FORM);
  const [printLabelForm, setPrintLabelForm] = useState<PrintLabelFormState>(EMPTY_PRINT_LABEL_FORM);
  const [scanForm, setScanForm] = useState<ScanFormState>(EMPTY_SCAN_FORM);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; onConfirm: () => void } | null>(null);

  const selectedCylinderId = selectedCylinder?.id ?? "";

  const cylindersQuery = useQuery({
    queryKey: logisticsKeys.cylinders.list({ search, state: stateFilter, active: true }),
    queryFn: () => listCylinders({ search, state: stateFilter, active: true }),
  });
  const statesQuery = useQuery({ queryKey: logisticsKeys.states(), queryFn: listCylinderStates });
  const summaryQuery = useQuery({
    queryKey: logisticsKeys.cylinders.summary(),
    queryFn: listCylinderSummary,
  });
  const gasProductsQuery = useQuery({ queryKey: logisticsKeys.gasProducts(), queryFn: listGasProducts });
  const brandsQuery = useQuery({ queryKey: logisticsKeys.brands(), queryFn: listBrands });
  const gasCatalogQuery = useQuery({
    queryKey: [...productosKeys.products.all, "all-active"],
    queryFn: () => listAllProducts({ is_active: true }),
  });
  const brandCatalogQuery = useQuery({ queryKey: productosKeys.catalogs.brands, queryFn: listProductBrands });
  const sublineCatalogQuery = useQuery({ queryKey: productosKeys.catalogs.subline, queryFn: listSubline });
  const conditionsQuery = useQuery({ queryKey: logisticsKeys.conditions(), queryFn: listConditions });
  const serviceTypesQuery = useQuery({
    queryKey: logisticsKeys.serviceTypes(),
    queryFn: listServiceTypes,
    enabled: canServiceRead || canServiceManage,
  });

  const traceQuery = useQuery({
    queryKey: logisticsKeys.cylinders.trace(selectedCylinderId),
    queryFn: () => listCylinderTrace(selectedCylinderId),
    enabled: selectedCylinder !== null && canTrace,
  });
  const transitionsQuery = useQuery({
    queryKey: logisticsKeys.cylinders.allowedTransitions(selectedCylinderId),
    queryFn: () => getAllowedTransitions(selectedCylinderId),
    enabled: selectedCylinder !== null && canTransition,
  });
  const hydrotestsQuery = useQuery({
    queryKey: [...logisticsKeys.cylinders.detail(selectedCylinderId), "hydrotests"],
    queryFn: () => listHydrotests(selectedCylinderId),
    enabled: selectedCylinder !== null,
  });
  const warrantiesQuery = useQuery({
    queryKey: [...logisticsKeys.cylinders.detail(selectedCylinderId), "warranties"],
    queryFn: () => listWarranties(selectedCylinderId),
    enabled: selectedCylinder !== null,
  });
  const retimbradosQuery = useQuery({
    queryKey: logisticsKeys.cylinders.retimbrados(selectedCylinderId),
    queryFn: () => listRetimbrados(selectedCylinderId),
    enabled: selectedCylinder !== null,
  });
  const ownershipQuery = useQuery({
    queryKey: logisticsKeys.cylinders.ownership(selectedCylinderId),
    queryFn: () => listOwnership(selectedCylinderId),
    enabled: selectedCylinder !== null && canOwnershipRead,
  });
  const labelDataQuery = useQuery({
    queryKey: logisticsKeys.cylinders.labelData(selectedCylinderId),
    queryFn: () => getCylinderLabelData(selectedCylinderId),
    enabled: selectedCylinder !== null,
  });
  const labelHistoryQuery = useQuery({
    queryKey: logisticsKeys.cylinders.labelHistory(selectedCylinderId),
    queryFn: () => listLabelHistory(selectedCylinderId),
    enabled: selectedCylinder !== null,
  });
  const servicesQuery = useQuery({
    queryKey: logisticsKeys.cylinders.services(selectedCylinderId),
    queryFn: () => listCylinderServices(selectedCylinderId),
    enabled: selectedCylinder !== null && (canServiceRead || canServiceManage),
  });
  const scanLogsQuery = useQuery({
    queryKey: logisticsKeys.scans.list(),
    queryFn: listScanLogs,
    enabled: selectedCylinder !== null && canScanRead,
  });

  const gasById = useMemo(
    () => new Map((gasProductsQuery.data ?? []).map((item) => [item.id, item.name] as const)),
    [gasProductsQuery.data]
  );
  const productById = useMemo(
    () => new Map((gasCatalogQuery.data ?? []).map((item) => [item.id, item.name] as const)),
    [gasCatalogQuery.data]
  );
  const brandById = useMemo(
    () => new Map((brandsQuery.data ?? []).map((item) => [item.id, item.name] as const)),
    [brandsQuery.data]
  );
  const gasIdByCatalogKey = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of gasProductsQuery.data ?? []) {
      map.set(item.code, item.id);
      map.set(item.name, item.id);
      map.set(item.name.toUpperCase(), item.id);
    }
    return map;
  }, [gasProductsQuery.data]);
  const brandIdByCatalogKey = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of brandsQuery.data ?? []) {
      map.set(item.code, item.id);
      map.set(item.name, item.id);
      map.set(item.name.toUpperCase(), item.id);
    }
    return map;
  }, [brandsQuery.data]);
  const validGasIds = useMemo(() => new Set((gasProductsQuery.data ?? []).map((item) => item.id)), [gasProductsQuery.data]);

  const gasOptions = useMemo(() => {
    return (gasCatalogQuery.data ?? []).map((item) => ({
      id: item.id,
      name: `${item.sku} · ${item.name}`,
    }));
  }, [gasCatalogQuery.data]);

  const brandOptions = useMemo(() => {
    const options = (brandCatalogQuery.data ?? [])
      .map((item) => {
        const localId =
          brandIdByCatalogKey.get(item.code) ?? brandIdByCatalogKey.get(item.name) ?? brandIdByCatalogKey.get(item.name.toUpperCase());
        return localId ? { id: localId, name: `${item.code} · ${item.name}` } : null;
      })
      .filter((item): item is { id: string; name: string } => item !== null);
    const seen = new Set(options.map((item) => item.id));
    for (const item of brandsQuery.data ?? []) {
      if (!seen.has(item.id)) {
        options.push({ id: item.id, name: `${item.code} · ${item.name}` });
      }
    }
    return options;
  }, [brandCatalogQuery.data, brandIdByCatalogKey, brandsQuery.data]);
  const sublineOptions = useMemo(
    () =>
      (sublineCatalogQuery.data ?? []).map((item) => ({
        value: item.name,
        label: `${item.code} · ${item.name}`,
      })),
    [sublineCatalogQuery.data]
  );
  const serviceTypeById = useMemo(
    () => new Map((serviceTypesQuery.data ?? []).map((item) => [item.id, item.name] as const)),
    [serviceTypesQuery.data]
  );
  const summaryByState = useMemo(
    () => new Map((summaryQuery.data ?? []).map((item) => [item.state, item.count] as const)),
    [summaryQuery.data]
  );
  const filteredScans = useMemo(
    () => (scanLogsQuery.data ?? []).filter((item) => item.cylinder_id === selectedCylinder?.id),
    [scanLogsQuery.data, selectedCylinder?.id]
  );

  const productIdByGasId = useMemo(() => {
    const map = new Map<string, string>();
    for (const prod of gasCatalogQuery.data ?? []) {
      const lgId = gasIdByCatalogKey.get(prod.sku) ?? gasIdByCatalogKey.get(prod.name) ?? gasIdByCatalogKey.get(prod.name.toUpperCase());
      if (lgId) {
        map.set(lgId, prod.id);
      }
    }
    return map;
  }, [gasCatalogQuery.data, gasIdByCatalogKey]);

  const lgBrandIdByProdBrandId = useMemo(() => {
    const map = new Map<string, string>();
    for (const prodBrand of brandCatalogQuery.data ?? []) {
      const lgId = brandIdByCatalogKey.get(prodBrand.code) ?? brandIdByCatalogKey.get(prodBrand.name) ?? brandIdByCatalogKey.get(prodBrand.name.toUpperCase());
      if (lgId) {
        map.set(prodBrand.id, lgId);
      }
    }
    return map;
  }, [brandCatalogQuery.data, brandIdByCatalogKey]);

  const gasGroupIdRef = useRef(cylinderForm.gas_group_id);

  const invalidateCylinderCollections = async (cylinderId?: string) => {
    const tasks = [
      queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.summary() }),
    ];
    if (cylinderId) {
      tasks.push(
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.detail(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.trace(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.allowedTransitions(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.retimbrados(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.ownership(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.labelData(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.labelHistory(cylinderId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.services(cylinderId) })
      );
    }
    await Promise.all(tasks);
  };

  function resetCreateDialog() {
    setCylinderForm(EMPTY_CYLINDER_FORM);
    gasGroupIdRef.current = "";
    setCreateMeta(EMPTY_CYLINDER_CREATE_META);
    setPanelError(null);
    setIsCreateCustomerSearchOpen(false);
  }

  const createMutation = useMutation({
    mutationFn: createCylinder,
    onSuccess: async (cylinder) => {
      setSelectedCylinder(cylinder);
      setIsCreateOpen(false);
      resetCreateDialog();
      await invalidateCylinderCollections(cylinder.id);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ cylinderId, payload }: { cylinderId: string; payload: ReturnType<typeof buildCylinderPayload> }) =>
      updateCylinder(cylinderId, payload),
    onSuccess: async (cylinder) => {
      setSelectedCylinder(cylinder);
      setIsEditOpen(false);
      setDetailError(null);
      await invalidateCylinderCollections(cylinder.id);
    },
  });

  const transitionMutation = useMutation({
    mutationFn: ({ cylinderId, toState }: { cylinderId: string; toState: string }) =>
      transitionCylinder(cylinderId, { to_state: toState }),
    onSuccess: async (cylinder) => {
      setSelectedCylinder(cylinder);
      setNextState("");
      setDetailError(null);
      await invalidateCylinderCollections(cylinder.id);
    },
  });

  const hydrotestMutation = useMutation({
    mutationFn: () =>
      createHydrotest(selectedCylinderId, {
        test_date: hydrotestForm.test_date,
        status: hydrotestForm.status,
        notes: toNullable(hydrotestForm.notes),
      }),
    onSuccess: async () => {
      setIsHydrotestOpen(false);
      setHydrotestForm(EMPTY_HYDROTEST_FORM);
      setDetailError(null);
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const warrantyMutation = useMutation({
    mutationFn: () =>
      createWarranty(selectedCylinderId, {
        customer_id: warrantyForm.customer_id,
        warranty_type: warrantyForm.warranty_type,
        description: toNullable(warrantyForm.description),
      }),
    onSuccess: async () => {
      setIsWarrantyOpen(false);
      setWarrantyForm(EMPTY_WARRANTY_FORM);
      setDetailError(null);
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const retimbradoMutation = useMutation({
    mutationFn: () =>
      createRetimbrado(selectedCylinderId, {
        retimbrado_date: retimbradoForm.retimbrado_date,
        manufacture_code: toNullable(retimbradoForm.manufacture_code),
        manufacture_year: toIntegerOrNull(retimbradoForm.manufacture_year),
        serial_number: toNullable(retimbradoForm.serial_number),
        weight_origin: toNumberOrNull(retimbradoForm.weight_origin),
        weight_current: toNumberOrNull(retimbradoForm.weight_current),
        service_pressure: toNumberOrNull(retimbradoForm.service_pressure),
        test_pressure: toNumberOrNull(retimbradoForm.test_pressure),
        approval_number: toNullable(retimbradoForm.approval_number),
        danger_class: toNullable(retimbradoForm.danger_class),
        marking1: toNullable(retimbradoForm.marking1),
        marking2: toNullable(retimbradoForm.marking2),
        package_format: toNullable(retimbradoForm.package_format),
        transport_code: toIntegerOrNull(retimbradoForm.transport_code),
        adr_label: toNullable(retimbradoForm.adr_label),
        adr_tunnel: toNullable(retimbradoForm.adr_tunnel),
        un_number: toNullable(retimbradoForm.un_number),
        food_registry: toNullable(retimbradoForm.food_registry),
        notes: toNullable(retimbradoForm.notes),
      }),
    onSuccess: async () => {
      setIsRetimbradoOpen(false);
      setRetimbradoForm(EMPTY_RETIMBRADO_FORM);
      setDetailError(null);
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const serviceMutation = useMutation({
    mutationFn: () =>
      createCylinderService(selectedCylinderId, {
        service_type_id: serviceForm.service_type_id,
        status: serviceForm.status,
        start_date: toNullable(serviceForm.start_date),
        end_date: toNullable(serviceForm.end_date),
        notes: toNullable(serviceForm.notes),
        purchase_price: toNumberOrNull(serviceForm.purchase_price),
        sale_price: toNumberOrNull(serviceForm.sale_price),
        stock_in: toNumberOrNull(serviceForm.stock_in),
        stock_out: toNumberOrNull(serviceForm.stock_out),
        group_code: toNullable(serviceForm.group_code),
        discount_pct: toNumberOrNull(serviceForm.discount_pct),
        discount_amount: toNumberOrNull(serviceForm.discount_amount),
        total_amount: toNumberOrNull(serviceForm.total_amount),
      }),
    onSuccess: async () => {
      setIsServiceOpen(false);
      setServiceForm(EMPTY_SERVICE_FORM);
      setDetailError(null);
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const serviceStatusMutation = useMutation({
    mutationFn: ({ serviceId, status }: { serviceId: string; status: string }) =>
      updateCylinderService(selectedCylinderId, serviceId, { status }),
    onSuccess: async () => {
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: (serviceId: string) => deleteCylinderService(selectedCylinderId, serviceId),
    onSuccess: async () => {
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const printLabelMutation = useMutation({
    mutationFn: () =>
      printLabel(selectedCylinderId, {
        origin: printLabelForm.origin,
        reason: toNullable(printLabelForm.reason),
        printer_name: toNullable(printLabelForm.printer_name),
        copies: Number(printLabelForm.copies || "1"),
      }),
    onSuccess: async () => {
      setIsPrintLabelOpen(false);
      setPrintLabelForm(EMPTY_PRINT_LABEL_FORM);
      setDetailError(null);
      await invalidateCylinderCollections(selectedCylinderId);
    },
  });

  const scanMutation = useMutation({
    mutationFn: () =>
      processScan({
        movement_id: scanForm.movement_id,
        barcode_serial: scanForm.barcode_serial,
        service_type: scanForm.service_type,
        gps_lat: toNumberOrNull(scanForm.gps_lat),
        gps_lng: toNumberOrNull(scanForm.gps_lng),
      }),
    onSuccess: async (log) => {
      setIsScanOpen(false);
      setScanForm(EMPTY_SCAN_FORM);
      setDetailError(null);
      await Promise.all([
        invalidateCylinderCollections(log.cylinder_id ?? selectedCylinderId),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.scans.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() }),
      ]);
    },
  });

  const hasMainError = Boolean(
    cylindersQuery.error ||
      statesQuery.error ||
      summaryQuery.error ||
      gasCatalogQuery.error ||
      gasProductsQuery.error ||
      brandsQuery.error
  );

  async function handleCreateCylinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    try {
      await createMutation.mutateAsync(buildCreateCylinderPayload(cylinderForm, createMeta));
    } catch (error) {
      setPanelError(error instanceof Error ? error.message : "No se pudo crear el envase.");
    }
  }

  async function handleUpdateCylinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCylinder) {
      return;
    }
    setDetailError(null);
    try {
      const payload = buildCylinderPayload(cylinderForm);
      await updateMutation.mutateAsync({
        cylinderId: selectedCylinder.id,
        payload,
      });
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo actualizar el envase.");
    }
  }

  async function handleTransition() {
    if (!selectedCylinder || !nextState) {
      return;
    }
    setDetailError(null);
    try {
      await transitionMutation.mutateAsync({ cylinderId: selectedCylinder.id, toState: nextState });
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo aplicar la transición.");
    }
  }

  async function handleHydrotest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await hydrotestMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la PH.");
    }
  }

  async function handleWarranty(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await warrantyMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la garantía.");
    }
  }

  async function handleRetimbrado(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await retimbradoMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar el retimbrado.");
    }
  }

  async function handleService(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await serviceMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar el servicio.");
    }
  }

  async function handlePrintLabel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await printLabelMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la impresión.");
    }
  }

  async function handleScan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await scanMutation.mutateAsync();
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo procesar el escaneo.");
    }
  }

  function openDetail(cylinder: LogisticsCylinder) {
    setSelectedCylinder(cylinder);
    const raw = cylinder.product_id ?? cylinder.gas_group_id ?? "";
    const mapped = cylinder.product_id ?? productIdByGasId.get(raw) ?? (validGasIds.has(raw) ? raw : "");
    gasGroupIdRef.current = mapped;
    setCylinderForm({
      ...buildCylinderFormState(cylinder),
      gas_group_id: mapped,
    });
    setNextState("");
    setDetailError(null);
    setIsDetailMenuOpen(true);
    setScanForm({
      ...EMPTY_SCAN_FORM,
      barcode_serial: cylinder.barcode2 || cylinder.barcode1 || cylinder.serial,
    });
  }

  function openEditDialog() {
    const raw = selectedCylinder.product_id ?? selectedCylinder.gas_group_id ?? "";
    const mapped = selectedCylinder.product_id ?? productIdByGasId.get(raw) ?? (validGasIds.has(raw) ? raw : "");
    const form = {
      ...buildCylinderFormState(selectedCylinder),
      gas_group_id: mapped,
    };
    gasGroupIdRef.current = form.gas_group_id;
    setCylinderForm(form);
    setIsEditOpen(true);
  }

  function closeDetailContext() {
    setSelectedCylinder(null);
    setDetailError(null);
    setIsEditOpen(false);
    setIsDetailMenuOpen(false);
    setSelectedViewSection(null);
  }

  function openViewSection(section: NonNullable<typeof selectedViewSection>) {
    setIsDetailMenuOpen(false);
    setSelectedViewSection(section);
  }

  function closeViewSection() {
    setSelectedViewSection(null);
    if (selectedCylinder) {
      setIsDetailMenuOpen(true);
    }
  }

  function closeViewSectionAndGoBack() {
    setSelectedViewSection(null);
    setIsDetailMenuOpen(true);
  }

  function handleCylinderFormChange(next: CylinderFormState) {
    const prevGasId = gasGroupIdRef.current;
    setCylinderForm(next);
    if (next.gas_group_id && next.gas_group_id !== prevGasId) {
      gasGroupIdRef.current = next.gas_group_id;
      getProduct(next.gas_group_id).then((product) => {
        setCylinderForm((current) => ({
          ...current,
          brand_id: lgBrandIdByProdBrandId.get(product.brand_id ?? "") ?? current.brand_id,
          adr_subline: product.subline_name ?? current.adr_subline,
        }));
      }).catch(() => {});
    }
  }

  return (
    <>
      <CylinderViewSectionDialog
        open={selectedViewSection !== null}
        section={selectedViewSection}
        cylinderId={selectedCylinderId}
        onBack={closeViewSectionAndGoBack}
        traceData={traceQuery.data ?? []}
        hydrotestsData={hydrotestsQuery.data ?? []}
        warrantiesData={warrantiesQuery.data ?? []}
        retimbradosData={retimbradosQuery.data ?? []}
        ownershipData={ownershipQuery.data ?? []}
        labelHistoryData={labelHistoryQuery.data ?? []}
        servicesData={servicesQuery.data ?? []}
        scanData={filteredScans}
        labelData={labelDataQuery.data ?? null}
        serviceTypeById={serviceTypeById}
      />
      <LogisticsSection
      title="Control de envases"
      description="Ficha completa del cilindro, trazabilidad, retimbrados, etiquetas, servicios y escaneo en campo."
      actions={canCreate ? <Button onClick={() => setIsCreateOpen(true)}>Nuevo envase</Button> : null}
    >
      {hasMainError ? (
        <Alert title="No se pudo cargar la vista principal">
          Revisa permisos o conectividad con el backend del plugin.
        </Alert>
      ) : null}

      <div className="overflow-x-auto">
        <div className="flex min-w-max gap-3">
          {[
            "CREADO_VACIO",
            "EN_ALMACEN_VACIO",
            "LLENADO_OK",
            "EN_RUTA",
            "EN_CLIENTE_LLENO",
            "OBSERVADO",
          ].map((state) => (
            <Card key={state} className="min-w-40">
              <CardContent className="space-y-2 p-4">
                <CylinderStateBadge state={state} />
                <p className="text-2xl font-semibold text-foreground">{summaryByState.get(state) ?? 0}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Consulta rápida</CardTitle>
          <CardDescription>Busca por serie, barcode, matrícula o ubicación.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Serie o barcode" />
          <Select value={stateFilter} onChange={(value) => setStateFilter(value)}
            placeholder="Todos los estados"
            options={(statesQuery.data ?? []).map((state) => ({ value: state.code, label: getCylinderStateLabel(state.code) }))} />
          <Button variant="secondary" onClick={() => { setSearch(""); setStateFilter(""); }}>
            Limpiar filtros
          </Button>
        </CardContent>
      </Card>

      <DataTable
        columns={[
          {
            key: "serial",
            header: "Envase",
            render: (row) => (
              <div className="space-y-1">
                <button
                  type="button"
                  onClick={() => openDetail(row)}
                  className="text-left font-medium text-cyan-300 hover:text-cyan-200"
                >
                  {row.serial}
                </button>
                <p className="text-xs text-muted-foreground">{row.description || "Sin descripción"}</p>
                <p className="text-xs text-muted-foreground">{row.barcode2 || row.barcode1 || "Sin barcode"}</p>
              </div>
            ),
          },
          {
            key: "gas",
            header: "Gas / marca",
            render: (row) => (
              <div className="space-y-1 text-sm text-foreground">
                <p>{productById.get(row.product_id ?? "") || gasById.get(row.gas_group_id ?? "") || "Sin gas"}</p>
                <p className="text-xs text-muted-foreground">{brandById.get(row.brand_id ?? "") || "Sin marca"}</p>
              </div>
            ),
          },
          {
            key: "state",
            header: "Estado",
            render: (row) => <CylinderStateBadge state={row.current_state} />,
          },
          {
            key: "ph",
            header: "PH / ADR",
            render: (row) => (
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>PH: {formatDate(row.next_hydrotest_date)}</p>
                <p>ADR: {row.adr_un_number || "-"}</p>
              </div>
            ),
          },
          {
            key: "location",
            header: "Ubicación",
            render: (row) => <span className="text-sm text-foreground">{row.location || "-"}</span>,
          },
          {
            key: "actions",
            header: "Acciones",
            render: (row) => (
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => openDetail(row)}>
                  Ver ficha
                </Button>
              </div>
            ),
          },
        ]}
        rows={cylindersQuery.data ?? []}
        rowKey={(row) => row.id}
        emptyMessage="Aún no hay envases registrados."
      />

      <CreateCylinderDialog
        open={isCreateOpen}
        onOpenChange={(open) => {
          setIsCreateOpen(open);
          if (!open) {
            resetCreateDialog();
          }
        }}
        cylinderForm={cylinderForm}
        onCylinderFormChange={handleCylinderFormChange}
        createMeta={createMeta}
        onCreateMetaChange={setCreateMeta}
        gasOptions={gasOptions}
        brandOptions={brandOptions}
        sublineOptions={sublineOptions}
        conditions={conditionsQuery.data ?? []}
        isPending={createMutation.isPending}
        error={panelError}
        onSubmit={handleCreateCylinder}
        onCustomerSearchClick={() => setIsCreateCustomerSearchOpen(true)}
      />

      <CustomerSearchDialog
        open={isCreateCustomerSearchOpen}
        onOpenChange={setIsCreateCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setCreateMeta((current) => ({
            ...current,
            customer_id: customer.id,
            customer_name: customer.display_name,
          }))
        }
      />

      <Dialog
        open={isDetailMenuOpen && selectedCylinder !== null}
        title={selectedCylinder ? `Ficha del envase ${selectedCylinder.serial}` : "Ficha del envase"}
        maxWidthClassName="max-w-[1600px]"
        onClose={closeDetailContext}
      >
        {selectedCylinder ? (
          <div className="space-y-4">
            {detailError ? <Alert title="Operación no completada">{detailError}</Alert> : null}

            <Card>
              <CardHeader>
                <CardTitle>Datos generales</CardTitle>
                <CardDescription>Resumen corto del envase antes de entrar a una función.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5 2xl:grid-cols-6 text-sm text-foreground">
                <div><span className="text-muted-foreground">Serial:</span> {selectedCylinder.serial}</div>
                <div><span className="text-muted-foreground">Estado:</span> <CylinderStateBadge state={selectedCylinder.current_state} /></div>
                <div><span className="text-muted-foreground">Gas:</span> {productById.get(selectedCylinder.product_id ?? "") || gasById.get(selectedCylinder.gas_group_id ?? "") || "-"}</div>
                <div><span className="text-muted-foreground">Marca:</span> {brandById.get(selectedCylinder.brand_id ?? "") || "-"}</div>
                <div><span className="text-muted-foreground">Barcode producto:</span> {selectedCylinder.barcode1 || "-"}</div>
                <div><span className="text-muted-foreground">Matrícula:</span> {selectedCylinder.barcode2 || "-"}</div>
                <div><span className="text-muted-foreground">Condición:</span> {selectedCylinder.condition || "-"}</div>
                <div><span className="text-muted-foreground">Ubicación:</span> {selectedCylinder.location || "-"}</div>
                <div><span className="text-muted-foreground">Contenido kg:</span> {selectedCylinder.content_kg?.toString() || "-"}</div>
                <div><span className="text-muted-foreground">Volumen m3:</span> {selectedCylinder.volume_m3?.toString() || "-"}</div>
                <div><span className="text-muted-foreground">Costo:</span> {selectedCylinder.cost?.toString() || "-"}</div>
                <div><span className="text-muted-foreground">Precio:</span> {selectedCylinder.price?.toString() || "-"}</div>
                <div><span className="text-muted-foreground">PH siguiente:</span> {formatDate(selectedCylinder.next_hydrotest_date) || "-"}</div>
                <div><span className="text-muted-foreground">ADR UN:</span> {selectedCylinder.adr_un_number || "-"}</div>
                <div><span className="text-muted-foreground">ADR etiqueta:</span> {selectedCylinder.adr_label || "-"}</div>
                <div><span className="text-muted-foreground">ADR mercancía:</span> {selectedCylinder.adr_merchandise || "-"}</div>
              </CardContent>
            </Card>

            {!selectedCylinder.barcode2 ? (
              <Alert title="Falta matrícula de etiqueta">Este envase aún no tiene `barcode2` para etiqueta y escaneo.</Alert>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle>Operativa</CardTitle>
                <CardDescription>Acciones para trabajar el envase.</CardDescription>
              </CardHeader>
              <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {canUpdate ? <button type="button" onClick={openEditDialog} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Editar ficha</p><p className="mt-1 text-xs text-muted-foreground">Actualiza los datos principales.</p></button> : null}
                  {canMaintenance ? <button type="button" onClick={() => setIsHydrotestOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar PH</p><p className="mt-1 text-xs text-muted-foreground">Nueva prueba hidrostática.</p></button> : null}
                  {canMaintenance ? <button type="button" onClick={() => setIsWarrantyOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar garantía</p><p className="mt-1 text-xs text-muted-foreground">Asocia una garantía comercial.</p></button> : null}
                  {canTransition ? <button type="button" onClick={() => setIsTransitionOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Transición operativa</p><p className="mt-1 text-xs text-muted-foreground">Cambia el estado del envase.</p></button> : null}
                  {canRetimbrado ? <button type="button" onClick={() => setIsRetimbradoOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar retimbrado</p><p className="mt-1 text-xs text-muted-foreground">Carga la ficha técnica del reestampado.</p></button> : null}
                  {canServiceManage ? <button type="button" onClick={() => setIsServiceOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Agregar servicio</p><p className="mt-1 text-xs text-muted-foreground">Registra un servicio operativo.</p></button> : null}
                  {canLabelPrint ? <button type="button" onClick={() => setIsPrintLabelOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Imprimir etiqueta</p><p className="mt-1 text-xs text-muted-foreground">Genera el registro de impresión.</p></button> : null}
                  {canScan ? <button type="button" onClick={() => setIsScanOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Escanear</p><p className="mt-1 text-xs text-muted-foreground">Procesa validación con GPS.</p></button> : null}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Vista</CardTitle>
                <CardDescription>Abre una tabla específica con un clic.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button type="button" onClick={() => openViewSection("trace")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Trazabilidad de estado</p><p className="mt-1 text-xs text-muted-foreground">Transiciones registradas.</p></button>
                  <button type="button" onClick={() => openViewSection("ph")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">PH y garantías</p><p className="mt-1 text-xs text-muted-foreground">Mantenimiento legal y comercial.</p></button>
                  <button type="button" onClick={() => openViewSection("retimbrados")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Retimbrados</p><p className="mt-1 text-xs text-muted-foreground">Ficha técnica del reestampado.</p></button>
                  <button type="button" onClick={() => openViewSection("custody")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Custodia e impresión</p><p className="mt-1 text-xs text-muted-foreground">Tenencia y etiquetas impresas.</p></button>
                  <button type="button" onClick={() => openViewSection("services")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Servicios y escaneos</p><p className="mt-1 text-xs text-muted-foreground">Mantenimiento y eventos de campo.</p></button>
                  <button type="button" onClick={() => openViewSection("label")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Etiqueta operativa</p><p className="mt-1 text-xs text-muted-foreground">Resumen rápido para impresión.</p></button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </Dialog>

      <Dialog
        open={isFullDetailOpen && selectedCylinder !== null}
        title={selectedCylinder ? `Ficha del envase ${selectedCylinder.serial}` : "Ficha del envase"}
        description="Detalle completo del envase con trazabilidad y operación asociada."
        maxWidthClassName="max-w-[1600px]"
        onClose={closeDetailContext}
      >
        {selectedCylinder ? (
          <div className="space-y-6">
            {detailError ? <Alert title="Operación no completada">{detailError}</Alert> : null}

            {!selectedCylinder.barcode2 ? (
              <Alert title="Falta matrícula de etiqueta">Este envase aún no tiene `barcode2` para etiqueta y escaneo.</Alert>
            ) : null}

            {!selectedCylinder.next_hydrotest_date ? (
              <Alert title="PH pendiente">Este envase no tiene una PH vigente registrada.</Alert>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <CylinderStateBadge state={selectedCylinder.current_state} />
              {canUpdate ? <Button variant="secondary" onClick={openEditDialog}>Editar ficha</Button> : null}
              {canMaintenance ? <Button variant="secondary" onClick={() => setIsHydrotestOpen(true)}>Registrar PH</Button> : null}
              {canMaintenance ? <Button variant="secondary" onClick={() => setIsWarrantyOpen(true)}>Registrar garantía</Button> : null}
              {canRetimbrado ? <Button variant="secondary" onClick={() => setIsRetimbradoOpen(true)}>Registrar retimbrado</Button> : null}
              {canServiceManage ? <Button variant="secondary" onClick={() => setIsServiceOpen(true)}>Agregar servicio</Button> : null}
              {canLabelPrint ? <Button variant="secondary" onClick={() => setIsPrintLabelOpen(true)}>Imprimir etiqueta</Button> : null}
              {canScan ? <Button variant="secondary" onClick={() => setIsScanOpen(true)}>Escanear</Button> : null}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Datos generales</CardTitle>
                <CardDescription>Identidad física, atributos comerciales y datos ADR.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 2xl:grid-cols-8">
                <InfoBlock label="Serial" value={selectedCylinder.serial} />
                <InfoBlock label="Descripción" value={selectedCylinder.description} />
                <InfoBlock label="Barcode producto" value={selectedCylinder.barcode1} />
                <InfoBlock label="Matrícula" value={selectedCylinder.barcode2} />
                <InfoBlock label="Gas" value={productById.get(selectedCylinder.product_id ?? "") || gasById.get(selectedCylinder.gas_group_id ?? "") || null} />
                <InfoBlock label="Marca" value={brandById.get(selectedCylinder.brand_id ?? "") || null} />
                <InfoBlock label="Condición" value={selectedCylinder.condition} />
                <InfoBlock label="Ubicación" value={selectedCylinder.location} />
                <InfoBlock label="Contenido kg" value={selectedCylinder.content_kg?.toString() ?? null} />
                <InfoBlock label="Volumen m3" value={selectedCylinder.volume_m3?.toString() ?? null} />
                <InfoBlock label="Costo" value={selectedCylinder.cost?.toString() ?? null} />
                <InfoBlock label="Precio" value={selectedCylinder.price?.toString() ?? null} />
                <InfoBlock label="PH siguiente" value={formatDate(selectedCylinder.next_hydrotest_date)} />
                <InfoBlock label="ADR UN" value={selectedCylinder.adr_un_number} />
                <InfoBlock label="ADR etiqueta" value={selectedCylinder.adr_label} />
                <InfoBlock label="ADR mercancía" value={selectedCylinder.adr_merchandise} />
              </CardContent>
            </Card>

            {canTransition ? (
              <Card>
                <CardHeader>
                  <CardTitle>Transición operativa</CardTitle>
                  <CardDescription>Aplica la siguiente transición válida del state machine.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-[1fr_auto]">
                  <Select value={nextState} onChange={(value) => setNextState(value)}
                    placeholder="Selecciona estado destino"
                    options={(transitionsQuery.data ?? []).map((item) => ({ value: item.to_state, label: getCylinderStateLabel(item.to_state) }))} />
                  <Button onClick={handleTransition} disabled={!nextState || transitionMutation.isPending}>
                    Aplicar transición
                  </Button>
                </CardContent>
              </Card>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle>Etiqueta operativa</CardTitle>
                <CardDescription>Resumen para impresión y verificación rápida en campo.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
                <InfoBlock label="Gas" value={labelDataQuery.data?.gas_product_name ?? null} />
                <InfoBlock label="Marca" value={labelDataQuery.data?.brand_name ?? null} />
                <InfoBlock label="Aprobación" value={labelDataQuery.data?.approval_number ?? null} />
                <InfoBlock label="Clase peligro" value={labelDataQuery.data?.danger_class ?? null} />
                <InfoBlock label="Nro ONU" value={labelDataQuery.data?.un_number ?? null} />
                <InfoBlock label="Última impresión" value={labelDataQuery.data?.label_origin ?? null} />
              </CardContent>
            </Card>

            <DataCard
              title="Trazabilidad de estado"
              description="Cada transición registrada sobre el cilindro."
              table={
                <DataTable
                  columns={[
                    { key: "when", header: "Fecha", render: (row) => formatDateTime(row.created_at) },
                    {
                      key: "change",
                      header: "Cambio",
                      render: (row) => (
                        <span className="text-sm text-foreground">
                          {row.from_state ? getCylinderStateLabel(row.from_state) : "Inicio"} → {getCylinderStateLabel(row.to_state)}
                        </span>
                      ),
                    },
                    { key: "origin", header: "Origen", render: (row) => row.origin || "-" },
                    { key: "notes", header: "Notas", render: (row) => row.notes || "-" },
                  ]}
                  rows={traceQuery.data ?? []}
                  rowKey={(row) => String(row.id)}
                  emptyMessage="Aún no hay trazas registradas."
                />
              }
            />

            <DataCard
              title="PH y garantías"
              description="Historial de mantenimiento legal y comercial."
              table={
                <div className="grid gap-4 lg:grid-cols-2">
                  <DataTable
                    columns={[
                      { key: "test_date", header: "PH", render: (row) => row.test_date },
                      { key: "status", header: "Estado", render: (row) => row.status || "-" },
                      { key: "notes", header: "Notas", render: (row) => row.notes || "-" },
                    ]}
                    rows={hydrotestsQuery.data ?? []}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin PH registradas."
                  />
                  <DataTable
                    columns={[
                      { key: "customer", header: "Cliente", render: (row) => row.customer_name },
                      { key: "type", header: "Tipo", render: (row) => row.warranty_type },
                      { key: "status", header: "Estado", render: (row) => row.status },
                    ]}
                    rows={warrantiesQuery.data ?? []}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin garantías registradas."
                  />
                </div>
              }
            />

            <DataCard
              title="Retimbrados"
              description="Ficha técnica del reestampado del cilindro."
              table={
                <DataTable
                  columns={[
                    { key: "date", header: "Fecha", render: (row) => row.retimbrado_date },
                    { key: "approval", header: "Aprobación", render: (row) => row.approval_number || "-" },
                    { key: "pressure", header: "Presión prueba", render: (row) => row.test_pressure?.toString() || "-" },
                    { key: "onu", header: "ONU", render: (row) => row.un_number || "-" },
                  ]}
                  rows={retimbradosQuery.data ?? []}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin retimbrados registrados."
                />
              }
            />

            <DataCard
              title="Custodia e impresión"
              description="Historial de tenencia del envase y sus etiquetas impresas."
              table={
                <div className="grid gap-4 lg:grid-cols-2">
                  <DataTable
                    columns={[
                      { key: "date", header: "Fecha", render: (row) => formatDateTime(row.change_date) },
                      { key: "customer", header: "Custodio", render: (row) => row.customer_name || "-" },
                      { key: "condition", header: "Condición", render: (row) => row.condition || "-" },
                    ]}
                    rows={ownershipQuery.data ?? []}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin cambios de custodia."
                  />
                  <DataTable
                    columns={[
                      { key: "date", header: "Fecha", render: (row) => formatDateTime(row.printed_at) },
                      { key: "origin", header: "Origen", render: (row) => row.origin },
                      { key: "copies", header: "Copias", render: (row) => row.copies },
                      { key: "reason", header: "Motivo", render: (row) => row.reason || "-" },
                    ]}
                    rows={labelHistoryQuery.data ?? []}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin impresiones registradas."
                  />
                </div>
              }
            />

            <DataCard
              title="Servicios y escaneos"
              description="Mantenimiento del envase y eventos de escaneo en campo."
              table={
                <div className="grid gap-4 lg:grid-cols-2">
                  <DataTable
                    columns={[
                      {
                        key: "service",
                        header: "Servicio",
                        render: (row) => serviceTypeById.get(row.service_type_id) || "-",
                      },
                      { key: "status", header: "Estado", render: (row) => row.status },
                      { key: "total", header: "Total", render: (row) => row.total_amount?.toString() || "-" },
                      {
                        key: "actions",
                        header: "Acciones",
                        render: (row) => (
                          canServiceManage ? (
                            <DropdownMenu
                              align="end"
                              trigger={<Button variant="secondary" className="h-7 w-7 px-0 py-0">⋮</Button>}
                              items={[
                                ...(row.status !== "REALIZADO"
                                  ? [{ label: "Completar", onClick: () => serviceStatusMutation.mutate({ serviceId: row.id, status: "REALIZADO" }) } as DropdownItem]
                                  : []),
                                { label: "Eliminar", destructive: true, onClick: () => setConfirmDelete({ id: row.id, onConfirm: () => deleteServiceMutation.mutate(row.id) }) },
                              ]}
                            />
                          ) : null
                        ),
                      },
                    ]}
                    rows={servicesQuery.data ?? []}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin servicios registrados."
                  />
                  <DataTable
                    columns={[
                      { key: "date", header: "Fecha", render: (row) => formatDateTime(row.scanned_at) },
                      { key: "service", header: "Servicio", render: (row) => row.service_type },
                      { key: "result", header: "Resultado", render: (row) => row.result },
                      {
                        key: "gps",
                        header: "GPS",
                        render: (row) =>
                          row.gps_lat !== null && row.gps_lng !== null ? `${row.gps_lat}, ${row.gps_lng}` : "-",
                      },
                    ]}
                    rows={filteredScans}
                    rowKey={(row) => row.id}
                    emptyMessage="Sin escaneos registrados."
                  />
                </div>
              }
            />
          </div>
        ) : null}
      </Dialog>

      <EditCylinderDialog
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
        cylinderForm={cylinderForm}
        onCylinderFormChange={handleCylinderFormChange}
        gasOptions={gasOptions}
        brandOptions={brandOptions}
        sublineOptions={sublineOptions}
        conditions={conditionsQuery.data ?? []}
        isPending={updateMutation.isPending}
        serial={selectedCylinder?.serial ?? ""}
        onSubmit={handleUpdateCylinder}
      />

      <Dialog
        open={isHydrotestOpen}
        title="Registrar PH"
        description="Actualiza la prueba hidrostática vigente del envase."
        onClose={() => setIsHydrotestOpen(false)}
      >
        <form className="space-y-4" onSubmit={handleHydrotest}>
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Fecha de PH">
              <Input type="date" value={hydrotestForm.test_date} onChange={(event) => setHydrotestForm((current) => ({ ...current, test_date: event.target.value }))} />
            </Field>
            <Field label="Estado">
              <Input value={hydrotestForm.status} onChange={(event) => setHydrotestForm((current) => ({ ...current, status: event.target.value }))} />
            </Field>
          </div>
          <Field label="Notas">
            <Textarea rows={4} value={hydrotestForm.notes} onChange={(event) => setHydrotestForm((current) => ({ ...current, notes: event.target.value }))} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsHydrotestOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={hydrotestMutation.isPending}>Registrar PH</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isWarrantyOpen} title="Registrar garantía" description="Asocia la garantía comercial del envase." onClose={() => setIsWarrantyOpen(false)}>
        <form className="space-y-4" onSubmit={handleWarranty}>
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Cliente">
              <Button type="button" variant="secondary" onClick={() => setIsWarrantyCustomerSearchOpen(true)}>
                {warrantyForm.customer_name ? `${warrantyForm.customer_name} (${warrantyForm.customer_id})` : "Seleccionar cliente"}
              </Button>
            </Field>
            <Field label="Tipo">
              <Input value={warrantyForm.warranty_type} onChange={(event) => setWarrantyForm((current) => ({ ...current, warranty_type: event.target.value }))} />
            </Field>
          </div>
          <Field label="Detalle">
            <Textarea rows={4} value={warrantyForm.description} onChange={(event) => setWarrantyForm((current) => ({ ...current, description: event.target.value }))} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsWarrantyOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={warrantyMutation.isPending}>Registrar garantía</Button>
          </div>
        </form>
      </Dialog>

      <CustomerSearchDialog
        open={isWarrantyCustomerSearchOpen}
        onOpenChange={setIsWarrantyCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setWarrantyForm((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))
        }
      />

      <Dialog open={isRetimbradoOpen} title="Registrar retimbrado" description="Carga la ficha técnica del retimbrado del envase." onClose={() => setIsRetimbradoOpen(false)}>
        <form className="space-y-4" onSubmit={handleRetimbrado}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <Field label="Fecha"><Input type="date" value={retimbradoForm.retimbrado_date} onChange={(event) => setRetimbradoForm((current) => ({ ...current, retimbrado_date: event.target.value }))} /></Field>
            <Field label="Código fabricación"><Input value={retimbradoForm.manufacture_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_code: event.target.value }))} /></Field>
            <Field label="Año"><Input type="number" value={retimbradoForm.manufacture_year} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_year: event.target.value }))} /></Field>
            <Field label="Nro bombona"><Input value={retimbradoForm.serial_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, serial_number: event.target.value }))} /></Field>
            <Field label="Peso origen"><Input type="number" value={retimbradoForm.weight_origin} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_origin: event.target.value }))} /></Field>
            <Field label="Peso actual"><Input type="number" value={retimbradoForm.weight_current} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_current: event.target.value }))} /></Field>
            <Field label="Presión servicio"><Input type="number" value={retimbradoForm.service_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, service_pressure: event.target.value }))} /></Field>
            <Field label="Presión prueba"><Input type="number" value={retimbradoForm.test_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, test_pressure: event.target.value }))} /></Field>
            <Field label="Nro aprobación"><Input value={retimbradoForm.approval_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, approval_number: event.target.value }))} /></Field>
            <Field label="Clase peligro"><Input value={retimbradoForm.danger_class} onChange={(event) => setRetimbradoForm((current) => ({ ...current, danger_class: event.target.value }))} /></Field>
            <Field label="Marcado 1"><Input value={retimbradoForm.marking1} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking1: event.target.value }))} /></Field>
            <Field label="Marcado 2"><Input value={retimbradoForm.marking2} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking2: event.target.value }))} /></Field>
            <Field label="Formato bulto"><Input value={retimbradoForm.package_format} onChange={(event) => setRetimbradoForm((current) => ({ ...current, package_format: event.target.value }))} /></Field>
            <Field label="Transporte"><Input type="number" value={retimbradoForm.transport_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, transport_code: event.target.value }))} /></Field>
            <Field label="Etiqueta ADR"><Input value={retimbradoForm.adr_label} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_label: event.target.value }))} /></Field>
            <Field label="Túnel ADR"><Input value={retimbradoForm.adr_tunnel} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_tunnel: event.target.value }))} /></Field>
            <Field label="Nro ONU"><Input value={retimbradoForm.un_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, un_number: event.target.value }))} /></Field>
            <Field label="Registro alimentario"><Input value={retimbradoForm.food_registry} onChange={(event) => setRetimbradoForm((current) => ({ ...current, food_registry: event.target.value }))} /></Field>
          </div>
          <Field label="Notas"><Textarea rows={4} value={retimbradoForm.notes} onChange={(event) => setRetimbradoForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsRetimbradoOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={retimbradoMutation.isPending}>Registrar retimbrado</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isServiceOpen} title="Registrar servicio" description="Asocia un servicio operativo sobre el envase." onClose={() => setIsServiceOpen(false)}>
        <form className="space-y-4" onSubmit={handleService}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <Field label="Tipo servicio">
              <Select value={serviceForm.service_type_id} onChange={(value) => setServiceForm((current) => ({ ...current, service_type_id: value }))}
                placeholder="Selecciona"
                options={(serviceTypesQuery.data ?? []).map((item) => ({ value: item.id, label: item.name }))} />
            </Field>
            <Field label="Estado"><Input value={serviceForm.status} onChange={(event) => setServiceForm((current) => ({ ...current, status: event.target.value }))} /></Field>
            <Field label="Inicio"><Input type="datetime-local" value={serviceForm.start_date} onChange={(event) => setServiceForm((current) => ({ ...current, start_date: event.target.value }))} /></Field>
            <Field label="Fin"><Input type="datetime-local" value={serviceForm.end_date} onChange={(event) => setServiceForm((current) => ({ ...current, end_date: event.target.value }))} /></Field>
            <Field label="Precio compra"><Input type="number" value={serviceForm.purchase_price} onChange={(event) => setServiceForm((current) => ({ ...current, purchase_price: event.target.value }))} /></Field>
            <Field label="Precio venta"><Input type="number" value={serviceForm.sale_price} onChange={(event) => setServiceForm((current) => ({ ...current, sale_price: event.target.value }))} /></Field>
            <Field label="Stock ingreso"><Input type="number" value={serviceForm.stock_in} onChange={(event) => setServiceForm((current) => ({ ...current, stock_in: event.target.value }))} /></Field>
            <Field label="Stock egreso"><Input type="number" value={serviceForm.stock_out} onChange={(event) => setServiceForm((current) => ({ ...current, stock_out: event.target.value }))} /></Field>
            <Field label="Grupo"><Input value={serviceForm.group_code} onChange={(event) => setServiceForm((current) => ({ ...current, group_code: event.target.value }))} /></Field>
            <Field label="Desc %"><Input type="number" value={serviceForm.discount_pct} onChange={(event) => setServiceForm((current) => ({ ...current, discount_pct: event.target.value }))} /></Field>
            <Field label="Desc monto"><Input type="number" value={serviceForm.discount_amount} onChange={(event) => setServiceForm((current) => ({ ...current, discount_amount: event.target.value }))} /></Field>
            <Field label="Total"><Input type="number" value={serviceForm.total_amount} onChange={(event) => setServiceForm((current) => ({ ...current, total_amount: event.target.value }))} /></Field>
          </div>
          <Field label="Notas"><Textarea rows={4} value={serviceForm.notes} onChange={(event) => setServiceForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsServiceOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={serviceMutation.isPending}>Registrar servicio</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isPrintLabelOpen} title="Imprimir etiqueta" description="Registra la impresión operativa de la etiqueta del envase." onClose={() => setIsPrintLabelOpen(false)}>
        <form className="space-y-4" onSubmit={handlePrintLabel}>
          <div className="grid gap-3 md:grid-cols-3">
            <Field label="Origen">
              <Select value={printLabelForm.origin} onChange={(value) => setPrintLabelForm((current) => ({ ...current, origin: value }))}
                options={[
                  { value: "ALTA", label: "ALTA" },
                  { value: "REIMPRESION", label: "REIMPRESION" },
                  { value: "PLUS", label: "PLUS" },
                ]} />
            </Field>
            <Field label="Impresora"><Input value={printLabelForm.printer_name} onChange={(event) => setPrintLabelForm((current) => ({ ...current, printer_name: event.target.value }))} /></Field>
            <Field label="Copias"><Input type="number" value={printLabelForm.copies} onChange={(event) => setPrintLabelForm((current) => ({ ...current, copies: event.target.value }))} /></Field>
          </div>
          <Field label="Motivo"><Textarea rows={3} value={printLabelForm.reason} onChange={(event) => setPrintLabelForm((current) => ({ ...current, reason: event.target.value }))} /></Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsPrintLabelOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={printLabelMutation.isPending}>Registrar impresión</Button>
          </div>
        </form>
      </Dialog>

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

      <Dialog open={isScanOpen} title="Escaneo en campo" description="Procesa un escaneo con validación ADR/PH y GPS." onClose={() => setIsScanOpen(false)}>
        <form className="space-y-4" onSubmit={handleScan}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Field label="Movimiento"><Input value={scanForm.movement_id} onChange={(event) => setScanForm((current) => ({ ...current, movement_id: event.target.value }))} /></Field>
            <Field label="Barcode / serie"><Input value={scanForm.barcode_serial} onChange={(event) => setScanForm((current) => ({ ...current, barcode_serial: event.target.value }))} /></Field>
            <Field label="Servicio">
              <Select value={scanForm.service_type} onChange={(value) => setScanForm((current) => ({ ...current, service_type: value }))}
                options={[
                  { value: "VENTA", label: "VENTA" },
                  { value: "CANJE_ENTREGA", label: "CANJE_ENTREGA" },
                  { value: "CANJE_RECOJO", label: "CANJE_RECOJO" },
                  { value: "ALQUILER", label: "ALQUILER" },
                  { value: "DEVOLUCION", label: "DEVOLUCION" },
                  { value: "RECHAZO", label: "RECHAZO" },
                  { value: "SPOT", label: "SPOT" },
                ]} />
            </Field>
            <Field label="GPS lat"><Input type="number" value={scanForm.gps_lat} onChange={(event) => setScanForm((current) => ({ ...current, gps_lat: event.target.value }))} /></Field>
            <Field label="GPS lng"><Input type="number" value={scanForm.gps_lng} onChange={(event) => setScanForm((current) => ({ ...current, gps_lng: event.target.value }))} /></Field>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsScanOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={scanMutation.isPending}>Procesar escaneo</Button>
          </div>
        </form>
      </Dialog>

      <ConfirmDialog
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => {
          confirmDelete?.onConfirm();
          setConfirmDelete(null);
        }}
        title="Confirmar eliminación"
        description="¿Estás seguro de eliminar este servicio?"
        destructive
        confirmLabel="Eliminar"
      />
    </LogisticsSection>
    </>
  );
}
