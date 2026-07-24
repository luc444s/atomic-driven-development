import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listCotizaciones, getCotizacion, cotizacionKeys } from "../api";
import type { QuoteDraftDTO, QuoteDraftListItem } from "../types";

export function useDraftList() {
  const queryClient = useQueryClient();

  const list = useQuery({
    queryKey: cotizacionKeys.list(),
    queryFn: listCotizaciones,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: cotizacionKeys.list() });
  };

  return {
    drafts: list.data ?? [],
    isLoading: list.isLoading,
    invalidate,
  };
}

export function useDraftDetail(id: string | null) {
  return useQuery({
    queryKey: cotizacionKeys.detail(id ?? ""),
    queryFn: () => getCotizacion(id!),
    enabled: !!id,
  });
}

export type { QuoteDraftDTO, QuoteDraftListItem };
