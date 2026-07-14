import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import {
  listContracts,
  listContractHistory,
  listCoreDocumentVersionsForContract,
  listCoreSignatureSessionsForContract,
  listContractTypes,
  getContract,
} from "../../api/contracts";

export function useContractList(filters: {
  customer_id?: string;
  status?: string;
  type?: string;
}) {
  return useQuery({
    queryKey: ["logistics", "contracts", filters],
    queryFn: () => listContracts(filters),
  });
}

export function useContractDetail(contractId: string | null) {
  return useQuery({
    queryKey: ["logistics", "contracts", contractId],
    queryFn: () => getContract(contractId!),
    enabled: !!contractId,
  });
}

export function useContractTypes() {
  return useQuery({
    queryKey: ["logistics", "contract-types"],
    queryFn: listContractTypes,
  });
}

export function useContractHistory(contractId: string | null) {
  return useQuery({
    queryKey: ["logistics", "contracts", contractId, "history"],
    queryFn: () => listContractHistory(contractId!),
    enabled: !!contractId,
  });
}

export function useDocumentVersions(contractId: string | null) {
  return useQuery({
    queryKey: ["logistics", "contracts", contractId, "documents"],
    queryFn: () => listCoreDocumentVersionsForContract(contractId!),
    enabled: !!contractId,
  });
}

export function useSignatureSessions(contractId: string | null) {
  return useQuery({
    queryKey: ["logistics", "contracts", contractId, "signatures"],
    queryFn: () => listCoreSignatureSessionsForContract(contractId!),
    enabled: !!contractId,
  });
}
