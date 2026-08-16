import { useEffect, useState } from "react";
import { Badge } from "@systutor/shell/ui/badge";
import { Button } from "@systutor/shell/ui/button";
import { CorePdfViewer } from "@systutor/shell/ui/core-pdf-viewer";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Tabs, type Tab } from "@systutor/shell/ui/tabs";
import { getApiBaseUrl } from "@systutor/shell/api/client";
import { useAuthStore } from "../../../../../apps/web/src/features/auth/store";
import { ContractStatusBadge } from "./contract-status-badge";
import { formatDate, formatDateTime } from "../../cylinders/utils/formatters";
import {
  useContractHistory,
  useDocumentVersions,
  useSignatureSessions,
} from "../hooks/use-contract-data";
import {
  getCoreDocumentSignedDownload,
  getCoreDocumentDownloadUrl,
  type LogisticsCylinderContract,
} from "../../api/contracts";

function normalizeApiUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${getApiBaseUrl()}${path}`;
}

async function fetchLegacyPdfBlobUrl(path: string): Promise<string | null> {
  const token = useAuthStore.getState().token;
  if (!token) return null;

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(normalizeApiUrl(path), { headers });
  if (!response.ok) {
    throw new Error(`No se pudo abrir el PDF (${response.status})`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

function extractCoreDocumentVersionId(path: string | null): string | null {
  if (!path) return null;
  const pathname = new URL(normalizeApiUrl(path)).pathname;
  const match = pathname.match(/\/api\/v1\/core\/documents\/([^/]+)\/download$/);
  return match?.[1] ?? null;
}

function buildAbsoluteUrl(path: string): string {
  return normalizeApiUrl(path);
}

function useResolvedPdfUrl(url: string | null): string | null {
  const [resolvedUrl, setResolvedUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!url) {
      setResolvedUrl(null);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const documentVersionId = extractCoreDocumentVersionId(url);
        if (documentVersionId) {
          const signed = await getCoreDocumentSignedDownload(documentVersionId);
          if (cancelled) return;
          setResolvedUrl(buildAbsoluteUrl(signed.url));
          return;
        }
        const objectUrl = await fetchLegacyPdfBlobUrl(url);
        if (!objectUrl || cancelled) return;
        if (cancelled) return;
        setResolvedUrl(objectUrl);
      } catch {
        // ignore
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [url]);

  return resolvedUrl;
}

type Props = {
  contract: LogisticsCylinderContract;
  open: boolean;
  onClose: () => void;
};

const typeLabel = (value: string) =>
  ({ DAILY: "Diario", MONTHLY: "Mensual", ANNUAL: "Anual" }[value] || value);

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function displaySignerName(
  signerName: string | null,
  signerEmail: string | null,
  customerName: string | null
) {
  if (signerName && !uuidPattern.test(signerName)) return signerName;
  if (signerEmail) return signerEmail;
  return customerName || "Cliente";
}

export function ContractDetailDialog({
  contract,
  open,
  onClose,
}: Props) {
  const [tab, setTab] = useState("info");
  const historyQuery = useContractHistory(open ? contract.id : null);
  const versionsQuery = useDocumentVersions(open ? contract.id : null);
  const sessionsQuery = useSignatureSessions(open ? contract.id : null);
  const pdfUrl = open ? contract.contract_file_path ?? null : null;
  const pdfViewerUrl = useResolvedPdfUrl(pdfUrl);

  const openPdf = async (path: string) => {
    const documentVersionId = extractCoreDocumentVersionId(path);
    if (documentVersionId) {
      const signed = await getCoreDocumentSignedDownload(documentVersionId);
      window.open(buildAbsoluteUrl(signed.url), "_blank", "noopener,noreferrer");
      return;
    }
    const objectUrl = await fetchLegacyPdfBlobUrl(path);
    if (!objectUrl) return;
    window.open(objectUrl, "_blank", "noopener,noreferrer");
  };

  const tabs: Tab[] = [
    {
      value: "info",
      label: "Detalle",
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="font-medium">Estado:</span>{" "}
              <ContractStatusBadge status={contract.status} />
            </div>
            <div>
              <span className="font-medium">Tipo:</span>{" "}
              {typeLabel(contract.contract_type)}
            </div>
            <div>
              <span className="font-medium">Cliente:</span>{" "}
              {contract.customer_name || "-"}
            </div>
            <div>
              <span className="font-medium">Serie:</span>{" "}
              {contract.series || "-"}
            </div>
            <div>
              <span className="font-medium">Inicio:</span>{" "}
              {formatDate(contract.start_date)}
            </div>
            <div>
              <span className="font-medium">Fin:</span>{" "}
              {contract.end_date ? formatDate(contract.end_date) : "-"}
            </div>
            <div>
              <span className="font-medium">Cantidad:</span>{" "}
              {contract.quantity}
            </div>
            <div>
              <span className="font-medium">Precio unitario:</span>{" "}
              {contract.unit_price?.toFixed(2)}
            </div>
            <div>
              <span className="font-medium">Firmado:</span>{" "}
              {contract.signed_flag ? "Si" : "No"}
            </div>
            <div>
              <span className="font-medium">Tipo firma:</span>{" "}
              {contract.signature_type || "-"}
            </div>
            {contract.contract_file_path && (
              <div className="col-span-2">
                <span className="font-medium">Documento:</span>{" "}
                <button
                  type="button"
                  onClick={() => openPdf(contract.contract_file_path!)}
                  className="text-cyan-300 hover:text-cyan-200 underline"
                >
                  Abrir PDF contractual
                </button>
              </div>
            )}
            {contract.notes && (
              <div className="col-span-2">
                <span className="font-medium">Notas:</span> {contract.notes}
              </div>
            )}
            {contract.observations && (
              <div className="col-span-2">
                <span className="font-medium">Observaciones:</span>{" "}
                {contract.observations}
              </div>
            )}
          </div>

          <div className="border-t pt-3">
            <h4 className="mb-2 font-medium">Historial</h4>
            {historyQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">
                Cargando historial...
              </p>
            ) : (historyQuery.data?.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">
                Sin eventos registrados.
              </p>
            ) : (
              <div className="space-y-1 text-sm">
                {historyQuery.data?.map((event) => (
                  <div key={event.id} className="rounded border p-2">
                    <div className="font-medium">{event.event_type}</div>
                    <div className="text-muted-foreground">
                      {formatDateTime(event.occurred_at)}
                    </div>
                    {event.description ? <div>{event.description}</div> : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      value: "documentos",
      label: "Documentos",
      content: (
        <div className="space-y-4">
          {contract.contract_file_path && (
            <div>
              <h4 className="mb-2 font-medium">PDF actual</h4>
              <CorePdfViewer fileUrl={pdfViewerUrl} loadingMessage="Cargando PDF..." />
            </div>
          )}
          <div>
            <h4 className="mb-2 font-medium">Versiones del documento</h4>
            {versionsQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">
                Cargando versiones...
              </p>
            ) : (versionsQuery.data?.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">
                Sin versiones registradas.
              </p>
            ) : (
              <div className="space-y-1 text-sm">
                {versionsQuery.data?.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between rounded border p-2"
                  >
                    <div>
                      <span className="font-medium">v{doc.version_number}</span>
                      <span className="ml-2 text-muted-foreground">
                        {doc.status}
                      </span>
                      {doc.title && (
                        <span className="ml-2 text-muted-foreground">
                          — {doc.title}
                        </span>
                      )}
                      <div className="text-xs text-muted-foreground">
                        {formatDateTime(doc.created_at)}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openPdf(getCoreDocumentDownloadUrl(doc.id))}
                    >
                      Ver PDF
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      value: "firmas",
      label: "Firmas",
      content: (
        <div className="space-y-4">
          <h4 className="font-medium">Sesiones de firma</h4>
          {sessionsQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">
              Cargando sesiones...
            </p>
          ) : (sessionsQuery.data?.length ?? 0) === 0 ? (
            <p className="text-sm text-muted-foreground">
              Sin sesiones de firma registradas.
            </p>
          ) : (
            <div className="space-y-2 text-sm">
              {sessionsQuery.data?.map((session) => (
                <div key={session.id} className="rounded border p-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {displaySignerName(
                        session.signer_name,
                        session.signer_email,
                        contract.customer_name
                      )}
                    </span>
                    <Badge
                      className={
                        session.status === "COMPLETED"
                          ? "bg-green-100 text-green-800"
                          : session.status === "PENDING"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-gray-100 text-gray-800"
                      }
                    >
                      {session.status === "COMPLETED"
                        ? "Completada"
                        : session.status === "PENDING"
                        ? "Pendiente"
                        : session.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Canal: {session.verification_channel} | Proveedor:{" "}
                    {session.provider}
                  </div>
                  {session.signer_role && (
                    <div className="text-xs text-muted-foreground">
                      Rol: {session.signer_role}
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground">
                    Creada: {formatDateTime(session.created_at)}
                    {session.completed_at &&
                      ` | Completada: ${formatDateTime(session.completed_at)}`}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <Dialog
      open={open}
      title={`Contrato ${contract.contract_number || "(borrador)"}`}
      maxWidthClassName="max-w-2xl"
      onClose={() => {
        setTab("info");
        onClose();
      }}
    >
      <Tabs value={tab} onChange={setTab} tabs={tabs} />
    </Dialog>
  );
}
