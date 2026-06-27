import { FormEvent, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../apps/web/src/lib/react-query";
import { useAuthStore } from "../../../apps/web/src/features/auth/store";
import { Alert } from "../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../apps/web/src/shared/ui/input";
import { CylinderStateBadge, getCylinderStateLabel } from "./CylinderStateBadge";
import { LogisticsSection } from "./components/LogisticsSection";
import {
  createCylinder,
  createCylinderService,
  createHydrotest,
  createRetimbrado,
  createWarranty,
  deleteCylinderService,
  getAllowedTransitions,
  getCylinderLabelData,
  listBrands,
  listCylinderServices,
  listCylinders,
  listCylinderStates,
  listCylinderSummary,
  listCylinderTrace,
  listGasProducts,
  listHydrotests,
  listLabelHistory,
  listOwnership,
  listRetimbrados,
  listScanLogs,
  listServiceTypes,
  listWarranties,
  logisticsKeys,
  LogisticsCylinder,
  printLabel,
  processScan,
  transitionCylinder,
  updateCylinder,
  updateCylinderService,
} from "./api";

const controlClassName =
  "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition placeholder:text-slate-500 focus:border-cyan-500";

type CylinderFormState = {
  serial: string;
  description: string;
  barcode1: string;
  barcode2: string;
  gas_group_id: string;
  content_kg: string;
  volume_m3: string;
  condition: string;
  brand_id: string;
  cost: string;
  price: string;
  country_code: string;
  box_number: string;
  is_service: boolean;
  manufacturer_date: string;
  manufacturer_code: string;
  manufacture_year: string;
  weight_origin: string;
  weight_current: string;
  last_hydrotest_date: string;
  next_hydrotest_date: string;
  adr_category: string;
  adr_un_number: string;
  adr_label: string;
  adr_package_type: string;
  adr_weight_kg: string;
  adr_merchandise: string;
  adr_tunnel: string;
  adr_subline: string;
  adr_factor: string;
  adr_points: string;
  adr_unit_measure: string;
  location: string;
  is_active: boolean;
};

type HydrotestFormState = {
  test_date: string;
  status: string;
  notes: string;
};

type WarrantyFormState = {
  customer_name: string;
  warranty_type: string;
  description: string;
};

type RetimbradoFormState = {
  retimbrado_date: string;
  manufacture_code: string;
  manufacture_year: string;
  serial_number: string;
  weight_origin: string;
  weight_current: string;
  service_pressure: string;
  test_pressure: string;
  approval_number: string;
  danger_class: string;
  marking1: string;
  marking2: string;
  package_format: string;
  transport_code: string;
  adr_label: string;
  adr_tunnel: string;
  un_number: string;
  food_registry: string;
  notes: string;
};

type ServiceFormState = {
  service_type_id: string;
  status: string;
  start_date: string;
  end_date: string;
  notes: string;
  purchase_price: string;
  sale_price: string;
  stock_in: string;
  stock_out: string;
  group_code: string;
  discount_pct: string;
  discount_amount: string;
  total_amount: string;
};

type PrintLabelFormState = {
  origin: string;
  reason: string;
  printer_name: string;
  copies: string;
};

type ScanFormState = {
  movement_id: string;
  barcode_serial: string;
  service_type: string;
  gps_lat: string;
  gps_lng: string;
};

const EMPTY_CYLINDER_FORM: CylinderFormState = {
  serial: "",
  description: "",
  barcode1: "",
  barcode2: "",
  gas_group_id: "",
  content_kg: "",
  volume_m3: "",
  condition: "NUEVO",
  brand_id: "",
  cost: "",
  price: "",
  country_code: "",
  box_number: "",
  is_service: false,
  manufacturer_date: "",
  manufacturer_code: "",
  manufacture_year: "",
  weight_origin: "",
  weight_current: "",
  last_hydrotest_date: "",
  next_hydrotest_date: "",
  adr_category: "",
  adr_un_number: "",
  adr_label: "",
  adr_package_type: "",
  adr_weight_kg: "",
  adr_merchandise: "",
  adr_tunnel: "",
  adr_subline: "",
  adr_factor: "",
  adr_points: "",
  adr_unit_measure: "",
  location: "",
  is_active: true,
};

const EMPTY_HYDROTEST_FORM: HydrotestFormState = {
  test_date: "",
  status: "VIGENTE",
  notes: "",
};

const EMPTY_WARRANTY_FORM: WarrantyFormState = {
  customer_name: "",
  warranty_type: "CAMBIO",
  description: "",
};

const EMPTY_RETIMBRADO_FORM: RetimbradoFormState = {
  retimbrado_date: "",
  manufacture_code: "",
  manufacture_year: "",
  serial_number: "",
  weight_origin: "",
  weight_current: "",
  service_pressure: "",
  test_pressure: "",
  approval_number: "",
  danger_class: "",
  marking1: "",
  marking2: "",
  package_format: "",
  transport_code: "",
  adr_label: "",
  adr_tunnel: "",
  un_number: "",
  food_registry: "",
  notes: "",
};

const EMPTY_SERVICE_FORM: ServiceFormState = {
  service_type_id: "",
  status: "PENDIENTE",
  start_date: "",
  end_date: "",
  notes: "",
  purchase_price: "",
  sale_price: "",
  stock_in: "",
  stock_out: "",
  group_code: "",
  discount_pct: "",
  discount_amount: "",
  total_amount: "",
};

const EMPTY_PRINT_LABEL_FORM: PrintLabelFormState = {
  origin: "ALTA",
  reason: "",
  printer_name: "",
  copies: "1",
};

const EMPTY_SCAN_FORM: ScanFormState = {
  movement_id: "",
  barcode_serial: "",
  service_type: "VENTA",
  gps_lat: "",
  gps_lng: "",
};

export function buildCylinderFormState(cylinder?: LogisticsCylinder | null): CylinderFormState {
  if (!cylinder) {
    return EMPTY_CYLINDER_FORM;
  }
  return {
    serial: cylinder.serial,
    description: cylinder.description ?? "",
    barcode1: cylinder.barcode1 ?? "",
    barcode2: cylinder.barcode2 ?? "",
    gas_group_id: cylinder.gas_group_id ?? "",
    content_kg: cylinder.content_kg?.toString() ?? "",
    volume_m3: cylinder.volume_m3?.toString() ?? "",
    condition: cylinder.condition ?? "",
    brand_id: cylinder.brand_id ?? "",
    cost: cylinder.cost?.toString() ?? "",
    price: cylinder.price?.toString() ?? "",
    country_code: cylinder.country_code ?? "",
    box_number: cylinder.box_number ?? "",
    is_service: cylinder.is_service,
    manufacturer_date: cylinder.manufacturer_date ?? "",
    manufacturer_code: cylinder.manufacturer_code ?? "",
    manufacture_year: cylinder.manufacture_year?.toString() ?? "",
    weight_origin: cylinder.weight_origin?.toString() ?? "",
    weight_current: cylinder.weight_current?.toString() ?? "",
    last_hydrotest_date: cylinder.last_hydrotest_date ?? "",
    next_hydrotest_date: cylinder.next_hydrotest_date ?? "",
    adr_category: cylinder.adr_category ?? "",
    adr_un_number: cylinder.adr_un_number ?? "",
    adr_label: cylinder.adr_label ?? "",
    adr_package_type: cylinder.adr_package_type ?? "",
    adr_weight_kg: cylinder.adr_weight_kg?.toString() ?? "",
    adr_merchandise: cylinder.adr_merchandise ?? "",
    adr_tunnel: cylinder.adr_tunnel ?? "",
    adr_subline: cylinder.adr_subline ?? "",
    adr_factor: cylinder.adr_factor?.toString() ?? "",
    adr_points: cylinder.adr_points?.toString() ?? "",
    adr_unit_measure: cylinder.adr_unit_measure ?? "",
    location: cylinder.location ?? "",
    is_active: cylinder.is_active,
  };
}

function toNullable(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function toNumberOrNull(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
}

function toIntegerOrNull(value: string) {
  const parsed = toNumberOrNull(value);
  return parsed === null ? null : Math.trunc(parsed);
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return value;
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function buildCylinderPayload(form: CylinderFormState) {
  return {
    serial: form.serial,
    description: toNullable(form.description),
    barcode1: toNullable(form.barcode1),
    barcode2: toNullable(form.barcode2),
    gas_group_id: toNullable(form.gas_group_id),
    content_kg: toNumberOrNull(form.content_kg),
    volume_m3: toNumberOrNull(form.volume_m3),
    condition: toNullable(form.condition),
    brand_id: toNullable(form.brand_id),
    cost: toNumberOrNull(form.cost),
    price: toNumberOrNull(form.price),
    country_code: toNullable(form.country_code),
    box_number: toNullable(form.box_number),
    is_service: form.is_service,
    manufacturer_date: toNullable(form.manufacturer_date),
    manufacturer_code: toNullable(form.manufacturer_code),
    manufacture_year: toIntegerOrNull(form.manufacture_year),
    weight_origin: toNumberOrNull(form.weight_origin),
    weight_current: toNumberOrNull(form.weight_current),
    last_hydrotest_date: toNullable(form.last_hydrotest_date),
    next_hydrotest_date: toNullable(form.next_hydrotest_date),
    adr_category: toNullable(form.adr_category),
    adr_un_number: toNullable(form.adr_un_number),
    adr_label: toNullable(form.adr_label),
    adr_package_type: toNullable(form.adr_package_type),
    adr_weight_kg: toNumberOrNull(form.adr_weight_kg),
    adr_merchandise: toNullable(form.adr_merchandise),
    adr_tunnel: toNullable(form.adr_tunnel),
    adr_subline: toNullable(form.adr_subline),
    adr_factor: toNumberOrNull(form.adr_factor),
    adr_points: toIntegerOrNull(form.adr_points),
    adr_unit_measure: toNullable(form.adr_unit_measure),
    location: toNullable(form.location),
    is_active: form.is_active,
  };
}

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
  const [isRetimbradoOpen, setIsRetimbradoOpen] = useState(false);
  const [isServiceOpen, setIsServiceOpen] = useState(false);
  const [isPrintLabelOpen, setIsPrintLabelOpen] = useState(false);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [nextState, setNextState] = useState("");
  const [cylinderForm, setCylinderForm] = useState<CylinderFormState>(EMPTY_CYLINDER_FORM);
  const [hydrotestForm, setHydrotestForm] = useState<HydrotestFormState>(EMPTY_HYDROTEST_FORM);
  const [warrantyForm, setWarrantyForm] = useState<WarrantyFormState>(EMPTY_WARRANTY_FORM);
  const [retimbradoForm, setRetimbradoForm] = useState<RetimbradoFormState>(EMPTY_RETIMBRADO_FORM);
  const [serviceForm, setServiceForm] = useState<ServiceFormState>(EMPTY_SERVICE_FORM);
  const [printLabelForm, setPrintLabelForm] = useState<PrintLabelFormState>(EMPTY_PRINT_LABEL_FORM);
  const [scanForm, setScanForm] = useState<ScanFormState>(EMPTY_SCAN_FORM);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

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
  const brandById = useMemo(
    () => new Map((brandsQuery.data ?? []).map((item) => [item.id, item.name] as const)),
    [brandsQuery.data]
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

  const createMutation = useMutation({
    mutationFn: createCylinder,
    onSuccess: async (cylinder) => {
      setSelectedCylinder(cylinder);
      setIsCreateOpen(false);
      setCylinderForm(EMPTY_CYLINDER_FORM);
      setPanelError(null);
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
        customer_name: warrantyForm.customer_name,
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
      gasProductsQuery.error ||
      brandsQuery.error
  );

  async function handleCreateCylinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    try {
      await createMutation.mutateAsync(buildCylinderPayload(cylinderForm));
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
      await updateMutation.mutateAsync({
        cylinderId: selectedCylinder.id,
        payload: buildCylinderPayload(cylinderForm),
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
    setCylinderForm(buildCylinderFormState(cylinder));
    setNextState("");
    setDetailError(null);
    setScanForm({
      ...EMPTY_SCAN_FORM,
      barcode_serial: cylinder.barcode2 || cylinder.barcode1 || cylinder.serial,
    });
  }

  function openEditDialog() {
    setCylinderForm(buildCylinderFormState(selectedCylinder));
    setIsEditOpen(true);
  }

  return (
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
                <p className="text-2xl font-semibold text-white">{summaryByState.get(state) ?? 0}</p>
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
          <select className={controlClassName} value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}>
            <option value="">Todos los estados</option>
            {(statesQuery.data ?? []).map((state) => (
              <option key={state.code} value={state.code}>
                {getCylinderStateLabel(state.code)}
              </option>
            ))}
          </select>
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
                <p className="text-xs text-slate-500">{row.description || "Sin descripción"}</p>
                <p className="text-xs text-slate-500">{row.barcode2 || row.barcode1 || "Sin barcode"}</p>
              </div>
            ),
          },
          {
            key: "gas",
            header: "Gas / marca",
            render: (row) => (
              <div className="space-y-1 text-sm text-slate-300">
                <p>{gasById.get(row.gas_group_id ?? "") || "Sin gas"}</p>
                <p className="text-xs text-slate-500">{brandById.get(row.brand_id ?? "") || "Sin marca"}</p>
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
              <div className="space-y-1 text-xs text-slate-400">
                <p>PH: {formatDate(row.next_hydrotest_date)}</p>
                <p>ADR: {row.adr_un_number || "-"}</p>
              </div>
            ),
          },
          {
            key: "location",
            header: "Ubicación",
            render: (row) => <span className="text-sm text-slate-300">{row.location || "-"}</span>,
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

      <Dialog
        open={isCreateOpen}
        title="Nuevo envase"
        description="Registra la ficha completa del cilindro."
        onClose={() => { setIsCreateOpen(false); setPanelError(null); }}
      >
        <form className="space-y-4" onSubmit={handleCreateCylinder}>
          <CylinderFormFields
            form={cylinderForm}
            gasProducts={gasProductsQuery.data ?? []}
            brands={brandsQuery.data ?? []}
            onChange={setCylinderForm}
            includeActivation={false}
          />
          {panelError ? <Alert title="No se pudo guardar">{panelError}</Alert> : null}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              Guardar envase
            </Button>
          </div>
        </form>
      </Dialog>

      <Dialog
        open={selectedCylinder !== null}
        title={selectedCylinder ? `Ficha del envase ${selectedCylinder.serial}` : "Ficha del envase"}
        description="Detalle completo del envase con trazabilidad y operación asociada."
        onClose={() => {
          setSelectedCylinder(null);
          setDetailError(null);
          setIsEditOpen(false);
        }}
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
              <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <InfoBlock label="Serial" value={selectedCylinder.serial} />
                <InfoBlock label="Descripción" value={selectedCylinder.description} />
                <InfoBlock label="Barcode producto" value={selectedCylinder.barcode1} />
                <InfoBlock label="Matrícula" value={selectedCylinder.barcode2} />
                <InfoBlock label="Gas" value={gasById.get(selectedCylinder.gas_group_id ?? "") || null} />
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
                  <select className={controlClassName} value={nextState} onChange={(event) => setNextState(event.target.value)}>
                    <option value="">Selecciona estado destino</option>
                    {(transitionsQuery.data ?? []).map((item) => (
                      <option key={item.id} value={item.to_state}>
                        {getCylinderStateLabel(item.to_state)}
                      </option>
                    ))}
                  </select>
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
              <CardContent className="grid gap-4 md:grid-cols-2">
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
                        <span className="text-sm text-slate-300">
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
                        render: (row) => serviceTypeById.get(row.service_type_id) || row.service_type_id,
                      },
                      { key: "status", header: "Estado", render: (row) => row.status },
                      { key: "total", header: "Total", render: (row) => row.total_amount?.toString() || "-" },
                      {
                        key: "actions",
                        header: "Acciones",
                        render: (row) => (
                          <div className="flex gap-2">
                            {canServiceManage && row.status !== "REALIZADO" ? (
                              <Button
                                variant="secondary"
                                onClick={() => serviceStatusMutation.mutate({ serviceId: row.id, status: "REALIZADO" })}
                              >
                                Completar
                              </Button>
                            ) : null}
                            {canServiceManage ? (
                              <Button variant="secondary" onClick={() => deleteServiceMutation.mutate(row.id)}>
                                Eliminar
                              </Button>
                            ) : null}
                          </div>
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

      <Dialog
        open={isEditOpen}
        title={selectedCylinder ? `Editar ${selectedCylinder.serial}` : "Editar envase"}
        description="Actualiza la ficha completa del envase."
        onClose={() => setIsEditOpen(false)}
      >
        <form className="space-y-4" onSubmit={handleUpdateCylinder}>
          <CylinderFormFields
            form={cylinderForm}
            gasProducts={gasProductsQuery.data ?? []}
            brands={brandsQuery.data ?? []}
            onChange={setCylinderForm}
            includeActivation
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsEditOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              Guardar cambios
            </Button>
          </div>
        </form>
      </Dialog>

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
            <textarea className={controlClassName} rows={4} value={hydrotestForm.notes} onChange={(event) => setHydrotestForm((current) => ({ ...current, notes: event.target.value }))} />
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
              <Input value={warrantyForm.customer_name} onChange={(event) => setWarrantyForm((current) => ({ ...current, customer_name: event.target.value }))} />
            </Field>
            <Field label="Tipo">
              <Input value={warrantyForm.warranty_type} onChange={(event) => setWarrantyForm((current) => ({ ...current, warranty_type: event.target.value }))} />
            </Field>
          </div>
          <Field label="Detalle">
            <textarea className={controlClassName} rows={4} value={warrantyForm.description} onChange={(event) => setWarrantyForm((current) => ({ ...current, description: event.target.value }))} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsWarrantyOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={warrantyMutation.isPending}>Registrar garantía</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isRetimbradoOpen} title="Registrar retimbrado" description="Carga la ficha técnica del retimbrado del envase." onClose={() => setIsRetimbradoOpen(false)}>
        <form className="space-y-4" onSubmit={handleRetimbrado}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <Field label="Fecha"><Input type="date" value={retimbradoForm.retimbrado_date} onChange={(event) => setRetimbradoForm((current) => ({ ...current, retimbrado_date: event.target.value }))} /></Field>
            <Field label="Código fabricación"><Input value={retimbradoForm.manufacture_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_code: event.target.value }))} /></Field>
            <Field label="Año fabricación"><Input type="number" value={retimbradoForm.manufacture_year} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_year: event.target.value }))} /></Field>
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
          <Field label="Notas"><textarea className={controlClassName} rows={4} value={retimbradoForm.notes} onChange={(event) => setRetimbradoForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
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
              <select className={controlClassName} value={serviceForm.service_type_id} onChange={(event) => setServiceForm((current) => ({ ...current, service_type_id: event.target.value }))}>
                <option value="">Selecciona</option>
                {(serviceTypesQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
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
          <Field label="Notas"><textarea className={controlClassName} rows={4} value={serviceForm.notes} onChange={(event) => setServiceForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
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
              <select className={controlClassName} value={printLabelForm.origin} onChange={(event) => setPrintLabelForm((current) => ({ ...current, origin: event.target.value }))}>
                <option value="ALTA">ALTA</option>
                <option value="REIMPRESION">REIMPRESION</option>
                <option value="PLUS">PLUS</option>
              </select>
            </Field>
            <Field label="Impresora"><Input value={printLabelForm.printer_name} onChange={(event) => setPrintLabelForm((current) => ({ ...current, printer_name: event.target.value }))} /></Field>
            <Field label="Copias"><Input type="number" value={printLabelForm.copies} onChange={(event) => setPrintLabelForm((current) => ({ ...current, copies: event.target.value }))} /></Field>
          </div>
          <Field label="Motivo"><textarea className={controlClassName} rows={3} value={printLabelForm.reason} onChange={(event) => setPrintLabelForm((current) => ({ ...current, reason: event.target.value }))} /></Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsPrintLabelOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={printLabelMutation.isPending}>Registrar impresión</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isScanOpen} title="Escaneo en campo" description="Procesa un escaneo con validación ADR/PH y GPS." onClose={() => setIsScanOpen(false)}>
        <form className="space-y-4" onSubmit={handleScan}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Field label="Movimiento"><Input value={scanForm.movement_id} onChange={(event) => setScanForm((current) => ({ ...current, movement_id: event.target.value }))} /></Field>
            <Field label="Barcode / serie"><Input value={scanForm.barcode_serial} onChange={(event) => setScanForm((current) => ({ ...current, barcode_serial: event.target.value }))} /></Field>
            <Field label="Servicio">
              <select className={controlClassName} value={scanForm.service_type} onChange={(event) => setScanForm((current) => ({ ...current, service_type: event.target.value }))}>
                {[
                  "VENTA",
                  "CANJE_ENTREGA",
                  "CANJE_RECOJO",
                  "ALQUILER",
                  "DEVOLUCION",
                  "RECHAZO",
                  "SPOT",
                ].map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
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
    </LogisticsSection>
  );
}

type CylinderFormFieldsProps = {
  form: CylinderFormState;
  gasProducts: Array<{ id: string; name: string }>;
  brands: Array<{ id: string; name: string }>;
  includeActivation: boolean;
  onChange: (next: CylinderFormState) => void;
};

function CylinderFormFields({ form, gasProducts, brands, includeActivation, onChange }: CylinderFormFieldsProps) {
  function updateField<Key extends keyof CylinderFormState>(key: Key, value: CylinderFormState[Key]) {
    onChange({ ...form, [key]: value });
  }

  return (
    <div className="space-y-4">
      <FormRow title="Identificación">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-2 xl:col-span-2" label="Serial"><Input value={form.serial} onChange={(event) => updateField("serial", event.target.value)} /></Field>
        <Field className="md:col-span-4 xl:col-span-4" label="Descripción"><Input value={form.description} onChange={(event) => updateField("description", event.target.value)} /></Field>
        <Field className="md:col-span-4 xl:col-span-4" label="Ubicación"><Input value={form.location} onChange={(event) => updateField("location", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Caja / lote"><Input value={form.box_number} onChange={(event) => updateField("box_number", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="Códigos y Clasificación">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-3 xl:col-span-3" label="Barcode producto"><Input value={form.barcode1} onChange={(event) => updateField("barcode1", event.target.value)} /></Field>
        <Field className="md:col-span-3 xl:col-span-3" label="Matrícula etiqueta"><Input value={form.barcode2} onChange={(event) => updateField("barcode2", event.target.value)} /></Field>
        <Field className="md:col-span-3 xl:col-span-3" label="Gas">
        <select className={controlClassName} value={form.gas_group_id} onChange={(event) => updateField("gas_group_id", event.target.value)}>
          <option value="">Sin asignar</option>
          {gasProducts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </Field>
        <Field className="md:col-span-3 xl:col-span-3" label="Marca">
        <select className={controlClassName} value={form.brand_id} onChange={(event) => updateField("brand_id", event.target.value)}>
          <option value="">Sin asignar</option>
          {brands.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </Field>
      </div>
      </FormRow>

      <FormRow title="Datos Comerciales y Uso">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-2 xl:col-span-2" label="Condición"><Input value={form.condition} onChange={(event) => updateField("condition", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Contenido kg"><Input type="number" value={form.content_kg} onChange={(event) => updateField("content_kg", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Volumen m3"><Input type="number" value={form.volume_m3} onChange={(event) => updateField("volume_m3", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="País"><Input value={form.country_code} onChange={(event) => updateField("country_code", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Costo"><Input type="number" value={form.cost} onChange={(event) => updateField("cost", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Precio"><Input type="number" value={form.price} onChange={(event) => updateField("price", event.target.value)} /></Field>
        <Field className="md:col-span-6 xl:col-span-5" label="Es servicio">
        <label className="flex items-center gap-2 text-sm text-slate-200">
          <input type="checkbox" checked={form.is_service} onChange={(event) => updateField("is_service", event.target.checked)} />
          Producto de servicio
        </label>
      </Field>
      </div>
      </FormRow>

      <FormRow title="Fabricación y PH">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-2 xl:col-span-2" label="Fecha fabricación"><Input type="date" value={form.manufacturer_date} onChange={(event) => updateField("manufacturer_date", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-3" label="Código fabricación"><Input value={form.manufacturer_code} onChange={(event) => updateField("manufacturer_code", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-1" label="Año fabricación"><Input type="number" value={form.manufacture_year} onChange={(event) => updateField("manufacture_year", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Peso origen"><Input type="number" value={form.weight_origin} onChange={(event) => updateField("weight_origin", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Peso actual"><Input type="number" value={form.weight_current} onChange={(event) => updateField("weight_current", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Última PH"><Input type="date" value={form.last_hydrotest_date} onChange={(event) => updateField("last_hydrotest_date", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Siguiente PH"><Input type="date" value={form.next_hydrotest_date} onChange={(event) => updateField("next_hydrotest_date", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="ADR">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-1 xl:col-span-1" label="Categoría"><Input value={form.adr_category} onChange={(event) => updateField("adr_category", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="UN"><Input value={form.adr_un_number} onChange={(event) => updateField("adr_un_number", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Etiqueta"><Input value={form.adr_label} onChange={(event) => updateField("adr_label", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Tipo bulto"><Input value={form.adr_package_type} onChange={(event) => updateField("adr_package_type", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Peso kg"><Input type="number" value={form.adr_weight_kg} onChange={(event) => updateField("adr_weight_kg", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Túnel"><Input value={form.adr_tunnel} onChange={(event) => updateField("adr_tunnel", event.target.value)} /></Field>
        <Field className="md:col-span-2 xl:col-span-2" label="Sublinea"><Input value={form.adr_subline} onChange={(event) => updateField("adr_subline", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Factor"><Input type="number" value={form.adr_factor} onChange={(event) => updateField("adr_factor", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Puntos"><Input type="number" value={form.adr_points} onChange={(event) => updateField("adr_points", event.target.value)} /></Field>
        <Field className="md:col-span-1 xl:col-span-1" label="Unidad"><Input value={form.adr_unit_measure} onChange={(event) => updateField("adr_unit_measure", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="Mercancía ADR">
      <div className="grid gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="md:col-span-6 xl:col-span-12" label="Mercancía"><Input value={form.adr_merchandise} onChange={(event) => updateField("adr_merchandise", event.target.value)} /></Field>
      </div>
      </FormRow>
      {includeActivation ? (
        <Field label="Activo">
          <label className="flex items-center gap-2 text-sm text-slate-200">
            <input type="checkbox" checked={form.is_active} onChange={(event) => updateField("is_active", event.target.checked)} />
            Envase activo
          </label>
        </Field>
      ) : null}
    </div>
  );
}

function FormRow({ title, children }: { title: string; children: any }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">{title}</p>
      {children}
    </div>
  );
}

type FieldProps = {
  label: string;
  children: any;
  className?: string;
};

function Field({ label, children, className }: FieldProps) {
  return (
    <label className={["space-y-1 text-sm text-slate-300", className ?? ""].join(" ")}>
      <span className="block text-xs uppercase tracking-[0.12em] text-slate-500">{label}</span>
      {children}
    </label>
  );
}

function InfoBlock({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="text-sm text-slate-200">{value || "-"}</p>
    </div>
  );
}

function DataCard({ title, description, table }: { title: string; description: string; table: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>{table}</CardContent>
    </Card>
  );
}
