import { useParams } from "../../../apps/web/src/lib/router";
import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

import { ModalCatalogo } from "./components/ModalCatalogo";
import { ModalDetalleProducto } from "./components/ModalDetalleProducto";
import { ModalNuevoProducto } from "./components/ModalNuevoProducto";
import { ProductSearchDialog } from "./components/ProductSearchDialog";
import { ProductListPage } from "./pages/ProductListPage";

export { ModalCatalogo, ModalDetalleProducto, ModalNuevoProducto, ProductSearchDialog };

function NuevoProductoFallback() {
  return <ModalNuevoProducto open onClose={() => window.history.back()} asPage />;
}

function EditarProductoFallback() {
  const { productId } = useParams();
  return <ModalNuevoProducto open productId={productId} onClose={() => window.history.back()} asPage />;
}

function DetalleProductoFallback() {
  const { productId } = useParams();
  return <ModalDetalleProducto open productId={productId!} onClose={() => window.history.back()} asPage />;
}

function CatalogoFallback() {
  return <ModalCatalogo open onClose={() => window.history.back()} asPage />;
}

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "productos",
    routes: [
      {
        path: "productos",
        title: "Productos",
        component: ProductListPage,
        requiredPermissions: ["productos.product.read"],
      },
      {
        path: "productos/new",
        title: "Nuevo producto",
        component: NuevoProductoFallback,
        requiredPermissions: ["productos.product.create"],
      },
      {
        path: "productos/:productId",
        title: "Editar producto",
        component: EditarProductoFallback,
        requiredPermissions: ["productos.product.update"],
      },
      {
        path: "productos/:productId/detail",
        title: "Detalle producto",
        component: DetalleProductoFallback,
        requiredPermissions: ["productos.product.read"],
      },
      {
        path: "productos/catalogs",
        title: "Catálogos productos",
        component: CatalogoFallback,
        requiredPermissions: ["productos.catalog.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/productos`,
        label: "Productos",
        requiredPermissions: ["productos.product.read"],
      },
    ],
    widgets: [],
  };
}
