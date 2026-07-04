import { FormEvent, useEffect, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Link, useNavigate, useParams } from "../../../../apps/web/src/lib/router";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { Checkbox, Input, Textarea } from "../../../../apps/web/src/shared/ui/input";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import {
  createProduct,
  getProduct,
  listBrands,
  listConditions,
  listGroups,
  listInsumoTypes,
  listLines,
  listStatus,
  listSubcategories,
  listSubline,
  listUnits,
  productosKeys,
  updateProduct,
} from "../api";
import { ProductosSection } from "../components/ProductosSection";
import type { ProductPayload } from "../types";

const EMPTY_PRODUCT: ProductPayload = {
  legacy_id: null,
  sku: "",
  name: "",
  description: null,
  short_description: null,
  line_id: "",
  subline_id: null,
  brand_id: null,
  insumo_type_id: null,
  unit_id: "",
  box_unit_id: null,
  qty_per_box: null,
  subcategory_id: null,
  group_id: null,
  status_code: "ACTIVO",
  condition_code: "PRODUCTO",
  weight_kg: null,
  content_m3: null,
  country_code: null,
  delivery_time: null,
  is_service: false,
  is_active: true,
};

const selectClassName =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition focus:border-ring";

export function ProductFormPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<ProductPayload>(EMPTY_PRODUCT);
  const [error, setError] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: productosKeys.products.detail(productId ?? "new"),
    queryFn: () => getProduct(productId!),
    enabled: Boolean(productId),
  });
  const linesQuery = useQuery({ queryKey: productosKeys.catalogs.lines, queryFn: listLines });
  const sublineQuery = useQuery({ queryKey: productosKeys.catalogs.subline, queryFn: listSubline });
  const brandsQuery = useQuery({ queryKey: productosKeys.catalogs.brands, queryFn: listBrands });
  const insumoTypesQuery = useQuery({ queryKey: productosKeys.catalogs.insumoTypes, queryFn: listInsumoTypes });
  const unitsQuery = useQuery({ queryKey: productosKeys.catalogs.units, queryFn: listUnits });
  const subcategoriesQuery = useQuery({ queryKey: productosKeys.catalogs.subcategories, queryFn: listSubcategories });
  const groupsQuery = useQuery({ queryKey: productosKeys.catalogs.groups, queryFn: listGroups });
  const statusQuery = useQuery({ queryKey: productosKeys.catalogs.status, queryFn: listStatus });
  const conditionsQuery = useQuery({ queryKey: productosKeys.catalogs.conditions, queryFn: listConditions });

  useEffect(() => {
    if (!detailQuery.data) {
      return;
    }
    setFormState({
      legacy_id: detailQuery.data.legacy_id,
      sku: detailQuery.data.sku,
      name: detailQuery.data.name,
      description: detailQuery.data.description,
      short_description: detailQuery.data.short_description,
      line_id: detailQuery.data.line_id,
      subline_id: detailQuery.data.subline_id,
      brand_id: detailQuery.data.brand_id,
      insumo_type_id: detailQuery.data.insumo_type_id,
      unit_id: detailQuery.data.unit_id,
      box_unit_id: detailQuery.data.box_unit_id,
      qty_per_box: detailQuery.data.qty_per_box,
      subcategory_id: detailQuery.data.subcategory_id,
      group_id: detailQuery.data.group_id,
      status_code: detailQuery.data.status_code,
      condition_code: detailQuery.data.condition_code,
      weight_kg: detailQuery.data.weight_kg,
      content_m3: detailQuery.data.content_m3,
      country_code: detailQuery.data.country_code,
      delivery_time: detailQuery.data.delivery_time,
      is_service: detailQuery.data.is_service,
      is_active: detailQuery.data.is_active,
    });
  }, [detailQuery.data]);

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: async (product) => {
      toast.success("Producto creado");
      await queryClient.invalidateQueries({ queryKey: productosKeys.products.all });
      navigate(`/app/productos/${product.id}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (payload: ProductPayload) => updateProduct(productId!, payload),
    onSuccess: async (product) => {
      toast.success("Producto actualizado");
      await queryClient.invalidateQueries({ queryKey: productosKeys.products.all });
      await queryClient.invalidateQueries({ queryKey: productosKeys.products.detail(product.id) });
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      if (productId) {
        await updateMutation.mutateAsync(formState);
      } else {
        await createMutation.mutateAsync(formState);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el producto.");
    }
  }

  return (
    <ProductosSection
      title={productId ? "Editar producto" : "Nuevo producto"}
      description="Primero se guarda la ficha maestra. Luego el detalle operativo permite gestionar barcodes, precios, costos, ADR, media y promociones."
      actions={
        productId ? (
          <Link to={`/app/productos/${productId}/detail`}>
            <Button variant="secondary">Abrir detalle operativo</Button>
          </Link>
        ) : undefined
      }
    >
      {error ? <Alert title="No se pudo guardar">{error}</Alert> : null}
      <form className="space-y-6" onSubmit={submitForm}>
        <Card>
          <CardHeader>
            <CardTitle>Ficha maestra</CardTitle>
            <CardDescription>Identidad, clasificación y relaciones del producto.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground">
                <span>SKU</span>
                <Input value={formState.sku} onChange={(event) => setFormState((current) => ({ ...current, sku: event.target.value }))} />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Legacy ID</span>
                <Input
                  type="number"
                  value={formState.legacy_id ?? ""}
                  onChange={(event) => setFormState((current) => ({ ...current, legacy_id: event.target.value ? Number(event.target.value) : null }))}
                />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Nombre</span>
                <Input value={formState.name} onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))} />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Descripción corta</span>
                <Input
                  value={formState.short_description ?? ""}
                  onChange={(event) => setFormState((current) => ({ ...current, short_description: event.target.value || null }))}
                />
              </label>
            </div>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Descripción</span>
              <Textarea
                className="min-h-24"
                value={formState.description ?? ""}
                onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value || null }))}
              />
            </label>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Línea</span>
                <select className={selectClassName} value={formState.line_id} onChange={(event) => setFormState((current) => ({ ...current, line_id: event.target.value }))}>
                  <option value="">Selecciona</option>
                  {(linesQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Sublínea</span>
                <select className={selectClassName} value={formState.subline_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, subline_id: event.target.value || null }))}>
                  <option value="">Sin sublínea</option>
                  {(sublineQuery.data ?? []).filter((item) => !formState.line_id || item.line_id === formState.line_id).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Marca</span>
                <select className={selectClassName} value={formState.brand_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, brand_id: event.target.value || null }))}>
                  <option value="">Sin marca</option>
                  {(brandsQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Tipo de insumo</span>
                <select className={selectClassName} value={formState.insumo_type_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, insumo_type_id: event.target.value || null }))}>
                  <option value="">Sin tipo</option>
                  {(insumoTypesQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Subcategoría</span>
                <select className={selectClassName} value={formState.subcategory_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, subcategory_id: event.target.value || null }))}>
                  <option value="">Sin subcategoría</option>
                  {(subcategoriesQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Grupo</span>
                <select className={selectClassName} value={formState.group_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, group_id: event.target.value || null }))}>
                  <option value="">Sin grupo</option>
                  {(groupsQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Unidad principal</span>
                <select className={selectClassName} value={formState.unit_id} onChange={(event) => setFormState((current) => ({ ...current, unit_id: event.target.value }))}>
                  <option value="">Selecciona</option>
                  {(unitsQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Unidad de caja</span>
                <select className={selectClassName} value={formState.box_unit_id ?? ""} onChange={(event) => setFormState((current) => ({ ...current, box_unit_id: event.target.value || null }))}>
                  <option value="">Sin unidad de caja</option>
                  {(unitsQuery.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Cantidad por caja</span>
                <Input type="number" value={formState.qty_per_box ?? ""} onChange={(event) => setFormState((current) => ({ ...current, qty_per_box: event.target.value ? Number(event.target.value) : null }))} />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Estado</span>
                <select className={selectClassName} value={formState.status_code} onChange={(event) => setFormState((current) => ({ ...current, status_code: event.target.value }))}>
                  {(statusQuery.data ?? []).map((item) => (
                    <option key={item.code} value={item.code}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Condición</span>
                <select className={selectClassName} value={formState.condition_code} onChange={(event) => setFormState((current) => ({ ...current, condition_code: event.target.value }))}>
                  {(conditionsQuery.data ?? []).map((item) => (
                    <option key={item.code} value={item.code}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Código país</span>
                <Input value={formState.country_code ?? ""} onChange={(event) => setFormState((current) => ({ ...current, country_code: event.target.value || null }))} />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-4">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Peso kg</span>
                <Input type="number" value={formState.weight_kg ?? ""} onChange={(event) => setFormState((current) => ({ ...current, weight_kg: event.target.value ? Number(event.target.value) : null }))} />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Contenido m3</span>
                <Input type="number" value={formState.content_m3 ?? ""} onChange={(event) => setFormState((current) => ({ ...current, content_m3: event.target.value ? Number(event.target.value) : null }))} />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Tiempo entrega</span>
                <Input value={formState.delivery_time ?? ""} onChange={(event) => setFormState((current) => ({ ...current, delivery_time: event.target.value || null }))} />
              </label>
              <label className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
                <Checkbox checked={formState.is_service} onChange={(event) => setFormState((current) => ({ ...current, is_service: event.target.checked }))} />
                Servicio
              </label>
            </div>
          </CardContent>
        </Card>

        {productId ? (
          <Card>
            <CardHeader>
              <CardTitle>Siguiente paso</CardTitle>
              <CardDescription>
                La gestión detallada de barcodes, precios, costos, impuestos, ADR, media y promociones se realiza en el detalle operativo.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to={`/app/productos/${productId}/detail`}>
                <Button variant="secondary">Ir al detalle operativo</Button>
              </Link>
            </CardContent>
          </Card>
        ) : null}

        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={() => navigate("/app/productos")}>Cancelar</Button>
          <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>Guardar ficha</Button>
        </div>
      </form>
    </ProductosSection>
  );
}
