import type { SessionWaybillVersion } from "../../api";

export function formatSessionWaybillDocumentKind(kind: SessionWaybillVersion["document_kind"]) {
  return kind === "OFFICIAL" ? "Documento oficial" : "Preview viva";
}

export function buildSessionWaybillHistoryLabel(version: Pick<SessionWaybillVersion, "document_kind" | "version">) {
  return `${formatSessionWaybillDocumentKind(version.document_kind)} v${version.version}`;
}
