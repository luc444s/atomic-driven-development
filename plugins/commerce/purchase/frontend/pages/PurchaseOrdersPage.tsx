import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { useRef, useState } from "react";
import { listAllProducts } from "../../../../productos/frontend/api";
import { OrdersPanel } from "./purchase/OrdersPanel";
import { ClaimsPanel, type ClaimsPanelHandle } from "./purchase/ClaimsPanel";
import { InvoicePanel, type InvoicePanelHandle } from "./purchase/InvoicePanel";
import {
  MerchandiseReturnDialog,
  type MerchandiseReturnDialogHandle,
} from "./purchase/MerchandiseReturnDialog";
import { ReceiptPanel, type ReceiptPanelHandle } from "./purchase/ReceiptPanel";

export function PurchaseOrdersPage() {
  const claimsRef = useRef<ClaimsPanelHandle>(null);
  const invoiceRef = useRef<InvoicePanelHandle>(null);
  const returnsRef = useRef<MerchandiseReturnDialogHandle>(null);
  const receiptRef = useRef<ReceiptPanelHandle>(null);
  const [error, setError] = useState<string | null>(null);
  const productsQuery = useQuery({
    queryKey: ["productos", "all-active"],
    queryFn: () => listAllProducts({ is_active: true }),
  });
  const products = productsQuery.data ?? [];

  return (
    <>
      <OrdersPanel
        error={error}
        setError={setError}
        products={products}
        onReceiveOrder={(orderId) => receiptRef.current?.openReceiveDialog(orderId)}
        onInvoicesOrder={(orderId) => invoiceRef.current?.openInvoicesDialog(orderId)}
        onClaimsOrder={(orderId) => claimsRef.current?.openClaimsDialog(orderId)}
        onReturnsOrder={(orderId) => returnsRef.current?.openReturnsDialog(orderId)}
      />
      <ClaimsPanel ref={claimsRef} setError={setError} />
      <InvoicePanel ref={invoiceRef} setError={setError} products={products} />
      <MerchandiseReturnDialog ref={returnsRef} products={products} />
      <ReceiptPanel ref={receiptRef} setError={setError} products={products} />
    </>
  );
}
