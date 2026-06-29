import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

import { ProductSearchDialog } from "./components/ProductSearchDialog";
import { CatalogManagerPage } from "./pages/CatalogManagerPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ProductFormPage } from "./pages/ProductFormPage";
import { ProductListPage } from "./pages/ProductListPage";

export { ProductSearchDialog };

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
        component: ProductFormPage,
        requiredPermissions: ["productos.product.create"],
      },
      {
        path: "productos/:productId",
        title: "Editar producto",
        component: ProductFormPage,
        requiredPermissions: ["productos.product.update"],
      },
      {
        path: "productos/:productId/detail",
        title: "Detalle producto",
        component: ProductDetailPage,
        requiredPermissions: ["productos.product.read"],
      },
      {
        path: "productos/catalogs",
        title: "Catálogos productos",
        component: CatalogManagerPage,
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
