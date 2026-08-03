import { useMemo } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import {
  listCylinderStates,
  listCylinderSummary,
  listGasProducts,
  listBrands,
  listConditions,
  listServiceTypes,
  listWarehouses,
  listCylinderServices,
  listHydrotests,
  listWarranties,
  listRetimbrados,
  listOwnership,
  listLabelHistory,
  getCylinderLabelData,
  listScanLogs,
  getAllowedTransitions,
  logisticsKeys,
} from "../../api";
import { listCylindersWithFilters } from "../../api/cylinder-list";
import {
  listAllProducts,
  listBrands as listProductBrands,
  listSubline,
  productosKeys,
} from "../../../../productos/frontend/api";

export interface CylinderDataPermissions {
  canCreate: boolean;
  canTrace: boolean;
  canTransition: boolean;
  canOwnershipRead: boolean;
  canServiceRead: boolean;
  canServiceManage: boolean;
  canScanRead: boolean;
  canWarehouseRead: boolean;
}

export interface UseCylinderDataInput {
  search: string;
  stateFilter: string;
  medicalOnly: boolean;
  page: number;
  perPage: number;
  selectedCylinderId: string;
  selectedCylinder: { id: string } | null;
  permissions: CylinderDataPermissions;
}

export function useCylinderData(input: UseCylinderDataInput) {
  const { search, stateFilter, medicalOnly, page, perPage, selectedCylinderId, selectedCylinder, permissions } = input;
  const selNotNull = selectedCylinder !== null;

  const cylindersQuery = useQuery({
    queryKey: logisticsKeys.cylinders.list({
      search,
      state: stateFilter,
      active: true,
      is_medical: medicalOnly || undefined,
      page,
      per_page: perPage,
    }),
    queryFn: () =>
      listCylindersWithFilters({
        search,
        state: stateFilter,
        active: true,
        is_medical: medicalOnly ? true : undefined,
        page,
        per_page: perPage,
      }),
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
    enabled: permissions.canServiceRead || permissions.canServiceManage,
  });
  const warehousesQuery = useQuery({
    queryKey: logisticsKeys.warehouses(),
    queryFn: listWarehouses,
    enabled: permissions.canCreate || permissions.canWarehouseRead,
  });

  const transitionsQuery = useQuery({
    queryKey: logisticsKeys.cylinders.allowedTransitions(selectedCylinderId),
    queryFn: () => getAllowedTransitions(selectedCylinderId),
    enabled: selNotNull && permissions.canTransition,
  });
  const hydrotestsQuery = useQuery({
    queryKey: [...logisticsKeys.cylinders.detail(selectedCylinderId), "hydrotests"],
    queryFn: () => listHydrotests(selectedCylinderId),
    enabled: selNotNull,
  });
  const warrantiesQuery = useQuery({
    queryKey: [...logisticsKeys.cylinders.detail(selectedCylinderId), "warranties"],
    queryFn: () => listWarranties(selectedCylinderId),
    enabled: selNotNull,
  });
  const retimbradosQuery = useQuery({
    queryKey: logisticsKeys.cylinders.retimbrados(selectedCylinderId),
    queryFn: () => listRetimbrados(selectedCylinderId),
    enabled: selNotNull,
  });
  const ownershipQuery = useQuery({
    queryKey: logisticsKeys.cylinders.ownership(selectedCylinderId),
    queryFn: () => listOwnership(selectedCylinderId),
    enabled: selNotNull && permissions.canOwnershipRead,
  });
  const labelDataQuery = useQuery({
    queryKey: logisticsKeys.cylinders.labelData(selectedCylinderId),
    queryFn: () => getCylinderLabelData(selectedCylinderId),
    enabled: selNotNull,
  });
  const labelHistoryQuery = useQuery({
    queryKey: logisticsKeys.cylinders.labelHistory(selectedCylinderId),
    queryFn: () => listLabelHistory(selectedCylinderId),
    enabled: selNotNull,
  });
  const servicesQuery = useQuery({
    queryKey: logisticsKeys.cylinders.services(selectedCylinderId),
    queryFn: () => listCylinderServices(selectedCylinderId),
    enabled: selNotNull && (permissions.canServiceRead || permissions.canServiceManage),
  });
  const scanLogsQuery = useQuery({
    queryKey: logisticsKeys.scans.list(),
    queryFn: listScanLogs,
    enabled: selNotNull && permissions.canScanRead,
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
  const validGasIds = useMemo(
    () => new Set((gasProductsQuery.data ?? []).map((item) => item.id)),
    [gasProductsQuery.data]
  );

  const gasOptions = useMemo(() => {
    return (gasCatalogQuery.data ?? []).map((item) => ({
      id: item.id,
      name: `${item.sku} · ${item.name}`,
      content_kg: item.content_kg,
    }));
  }, [gasCatalogQuery.data]);

  const brandOptions = useMemo(() => {
    const options = (brandCatalogQuery.data ?? [])
      .map((item) => {
        const localId =
          brandIdByCatalogKey.get(item.code) ??
          brandIdByCatalogKey.get(item.name) ??
          brandIdByCatalogKey.get(item.name.toUpperCase());
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
      const lgId =
        gasIdByCatalogKey.get(prod.sku) ??
        gasIdByCatalogKey.get(prod.name) ??
        gasIdByCatalogKey.get(prod.name.toUpperCase());
      if (lgId) {
        map.set(lgId, prod.id);
      }
    }
    return map;
  }, [gasCatalogQuery.data, gasIdByCatalogKey]);

  const lgBrandIdByProdBrandId = useMemo(() => {
    const map = new Map<string, string>();
    for (const prodBrand of brandCatalogQuery.data ?? []) {
      const lgId =
        brandIdByCatalogKey.get(prodBrand.code) ??
        brandIdByCatalogKey.get(prodBrand.name) ??
        brandIdByCatalogKey.get(prodBrand.name.toUpperCase());
      if (lgId) {
        map.set(prodBrand.id, lgId);
      }
    }
    return map;
  }, [brandCatalogQuery.data, brandIdByCatalogKey]);

  const hasMainError = Boolean(
    cylindersQuery.error ||
      statesQuery.error ||
      summaryQuery.error ||
      gasCatalogQuery.error ||
      gasProductsQuery.error ||
      brandsQuery.error
  );

  return {
    cylindersQuery,
    statesQuery,
    summaryQuery,
    gasProductsQuery,
    brandsQuery,
    gasCatalogQuery,
    brandCatalogQuery,
    sublineCatalogQuery,
    conditionsQuery,
    serviceTypesQuery,
    warehousesQuery,
    transitionsQuery,
    hydrotestsQuery,
    warrantiesQuery,
    retimbradosQuery,
    ownershipQuery,
    labelDataQuery,
    labelHistoryQuery,
    servicesQuery,
    scanLogsQuery,
    gasById,
    productById,
    brandById,
    gasIdByCatalogKey,
    brandIdByCatalogKey,
    validGasIds,
    gasOptions,
    brandOptions,
    sublineOptions,
    serviceTypeById,
    summaryByState,
    filteredScans,
    productIdByGasId,
    lgBrandIdByProdBrandId,
    hasMainError,
  };
}
