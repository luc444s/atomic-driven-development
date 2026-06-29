import { createElement } from "react";

import { useParams } from "../../../apps/web/src/lib/router";
import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

import { ModalAjusteStock } from "./components/ModalAjusteStock";
import { ModalConfigStock } from "./components/ModalConfigStock";
import { ModalDetalleStock } from "./components/ModalDetalleStock";
import { ModalTransferenciaStock } from "./components/ModalTransferenciaStock";
import { StockBalancePage } from "./pages/StockBalancePage";

function AjusteFallback() {
  return createElement(ModalAjusteStock, {
    open: true,
    onClose: () => window.history.back(),
    asPage: true,
  });
}

function TransferFallback() {
  return createElement(ModalTransferenciaStock, {
    open: true,
    onClose: () => window.history.back(),
    asPage: true,
  });
}

function ConfigFallback() {
  return createElement(ModalConfigStock, {
    open: true,
    onClose: () => window.history.back(),
    asPage: true,
  });
}

function DetalleFallback() {
  const { productId, warehouseId } = useParams();
  return createElement(ModalDetalleStock, {
    open: true,
    productId: productId!,
    warehouseId: warehouseId!,
    onClose: () => window.history.back(),
    asPage: true,
  });
}

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "stock",
    routes: [
      {
        path: "stock",
        title: "Stock",
        component: StockBalancePage,
        requiredPermissions: ["stock.balance.read"],
      },
      {
        path: "stock/adjust",
        title: "Ajustar stock",
        component: AjusteFallback,
        requiredPermissions: ["stock.balance.adjust"],
      },
      {
        path: "stock/transfer",
        title: "Transferir stock",
        component: TransferFallback,
        requiredPermissions: ["stock.transfer.create"],
      },
      {
        path: "stock/config",
        title: "Configurar stock",
        component: ConfigFallback,
        requiredPermissions: ["stock.config.manage"],
      },
      {
        path: "stock/:productId/:warehouseId",
        title: "Detalle stock",
        component: DetalleFallback,
        requiredPermissions: ["stock.balance.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/stock`,
        label: "Stock",
        requiredPermissions: ["stock.balance.read"],
      },
    ],
    widgets: [],
  };
}
