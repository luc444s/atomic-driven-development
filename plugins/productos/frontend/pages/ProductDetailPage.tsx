import { ChangeEvent, FormEvent, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Link, useParams } from "../../../../apps/web/src/lib/router";
import type { ProductAdr } from "../types";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { DropdownMenu, type DropdownItem } from "../../../../apps/web/src/shared/ui/dropdown-menu";
import { Checkbox, Input, Switch, Textarea } from "../../../../apps/web/src/shared/ui/input";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import {
  createProductAdr,
  createProductBarcode,
  createProductCost,
  createProductPrice,
  createProductPromotion,
  deleteProductBarcode,
  deleteProductMedia,
  deletePromotion,
  expireProductAdr,
  getProduct,
  listSubline,
  productosKeys,
  replaceProductTax,
  setPrimaryProductBarcode,
  setPrimaryProductMedia,
  toggleProduct,
  updateProductAdr,
  uploadProductMedia,
} from "../api";
import { ProductosSection } from "../components/ProductosSection";

const selectClassName =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition focus:border-ring";

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function ProductDetailPage() {
  const { productId } = useParams();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; onConfirm: () => void } | null>(null);
  const [barcodeType, setBarcodeType] = useState("INTERNAL");
  const [barcodeValue, setBarcodeValue] = useState("");
  const [priceList, setPriceList] = useState("UNITARIO");
  const [priceAmount, setPriceAmount] = useState("");
  const [priceCurrency, setPriceCurrency] = useState("");
  const [costType, setCostType] = useState("ACTUAL");
  const [costAmount, setCostAmount] = useState("");
  const [costCurrency, setCostCurrency] = useState("");
  const [taxValues, setTaxValues] = useState({
    igv_exempt: false,
    percepcion: "",
    comision_ext: "",
  });
  const [adrForm, setAdrForm] = useState({
    category: "",
    packaging_type: "",
    net_weight_kg: "",
    net_volume_m3: "",
    un_number: "",
    cargo_description: "",
    label: "",
    tunnel_restriction: "",
    subline_id: "",
    factor: "",
    points: "",
    unit_measure: "",
    valid_from: today(),
  });
  const [editAdr, setEditAdr] = useState<ProductAdr | null>(null);
  const [isEditAdrOpen, setIsEditAdrOpen] = useState(false);
  const [promotionForm, setPromotionForm] = useState({
    name: "",
    condition: "PORCENTAJE",
    qty_required: "",
    discount_percent: "",
    unit_price: "",
    box_price: "",
    valid_from: today(),
    valid_to: "",
    is_active: true,
  });
  const [mediaType, setMediaType] = useState("PHOTO");
  const [mediaFile, setMediaFile] = useState<File | null>(null);

  const detailQuery = useQuery({
    queryKey: productosKeys.products.detail(productId ?? "missing"),
    queryFn: () => getProduct(productId!),
    enabled: Boolean(productId),
  });
  const sublineQuery = useQuery({ queryKey: productosKeys.catalogs.subline, queryFn: listSubline });

  const currentTaxes = useMemo(() => {
    const map = new Map(detailQuery.data?.taxes.map((item) => [item.tax_type, item]) ?? []);
    return {
      igv: map.get("IGV"),
      percepcion: map.get("PERCEPCION"),
      comision: map.get("COMISION_EXT"),
    };
  }, [detailQuery.data?.taxes]);

  async function refreshDetail() {
    if (!productId) {
      return;
    }
    await queryClient.invalidateQueries({ queryKey: productosKeys.products.detail(productId) });
    await queryClient.invalidateQueries({ queryKey: productosKeys.products.all });
  }

  const barcodeMutation = useMutation({
    mutationFn: async () => {
      return createProductBarcode(productId!, {
        barcode_type: barcodeType,
        barcode: barcodeValue,
        is_primary: false,
        is_active: true,
      });
    },
    onSuccess: async () => {
      toast.success("Código de barras creado");
      setBarcodeValue("");
      await refreshDetail();
    },
  });

  const priceMutation = useMutation({
    mutationFn: async () =>
      createProductPrice(productId!, {
        price_list: priceList,
        amount: Number(priceAmount),
        currency: priceCurrency,
        valid_from: today(),
      }),
    onSuccess: async () => {
      toast.success("Precio creado");
      setPriceAmount("");
      await refreshDetail();
    },
  });

  const costMutation = useMutation({
    mutationFn: async () =>
      createProductCost(productId!, {
        cost_type: costType,
        amount: Number(costAmount),
        currency: costCurrency,
        valid_from: today(),
      }),
    onSuccess: async () => {
      toast.success("Costo creado");
      setCostAmount("");
      await refreshDetail();
    },
  });

  const taxMutation = useMutation({
    mutationFn: async () =>
      replaceProductTax(productId!, {
        configs: [
          { tax_type: "IGV", value: null, is_exempt: taxValues.igv_exempt, valid_from: today() },
          {
            tax_type: "PERCEPCION",
            value: taxValues.percepcion ? Number(taxValues.percepcion) : null,
            is_exempt: false,
            valid_from: today(),
          },
          {
            tax_type: "COMISION_EXT",
            value: taxValues.comision_ext ? Number(taxValues.comision_ext) : null,
            is_exempt: false,
            valid_from: today(),
          },
        ],
      }),
    onSuccess: async () => {
      toast.success("Impuesto actualizado");
      await refreshDetail();
    },
  });

  const adrMutation = useMutation({
    mutationFn: async () =>
      createProductAdr(productId!, {
        category: adrForm.category || null,
        packaging_type: adrForm.packaging_type || null,
        net_weight_kg: adrForm.net_weight_kg ? Number(adrForm.net_weight_kg) : null,
        net_volume_m3: adrForm.net_volume_m3 ? Number(adrForm.net_volume_m3) : null,
        un_number: adrForm.un_number || null,
        cargo_description: adrForm.cargo_description || null,
        label: adrForm.label || null,
        tunnel_restriction: adrForm.tunnel_restriction || null,
        subline_id: adrForm.subline_id || null,
        factor: adrForm.factor ? Number(adrForm.factor) : null,
        points: adrForm.points ? Number(adrForm.points) : null,
        unit_measure: adrForm.unit_measure || null,
        valid_from: adrForm.valid_from,
      }),
    onSuccess: async () => {
      toast.success("ADR registrado");
      await refreshDetail();
    },
  });

  const updateAdrMutation = useMutation({
    mutationFn: async () => {
      if (!editAdr) return;
      return updateProductAdr(productId!, editAdr.id, {
        source_product_id: editAdr.source_product_id,
        source_product_id_2: editAdr.source_product_id_2,
        source_product_id_3: editAdr.source_product_id_3,
        source_quantity_liters: editAdr.source_quantity_liters,
        category: editAdr.category,
        packaging_type: editAdr.packaging_type,
        net_weight_kg: editAdr.net_weight_kg,
        net_volume_m3: editAdr.net_volume_m3,
        un_number: editAdr.un_number,
        cargo_description: editAdr.cargo_description,
        label: editAdr.label,
        tunnel_restriction: editAdr.tunnel_restriction,
        subline_id: editAdr.subline_id,
        factor: editAdr.factor,
        points: editAdr.points,
        unit_measure: editAdr.unit_measure,
      });
    },
    onSuccess: async () => {
      toast.success("ADR actualizado");
      setIsEditAdrOpen(false);
      await refreshDetail();
    },
  });

  const promotionMutation = useMutation({
    mutationFn: async () =>
      createProductPromotion(productId!, {
        name: promotionForm.name || null,
        condition: promotionForm.condition,
        qty_required: promotionForm.qty_required ? Number(promotionForm.qty_required) : null,
        discount_percent: promotionForm.discount_percent ? Number(promotionForm.discount_percent) : null,
        unit_price: promotionForm.unit_price ? Number(promotionForm.unit_price) : null,
        box_price: promotionForm.box_price ? Number(promotionForm.box_price) : null,
        valid_from: promotionForm.valid_from,
        valid_to: promotionForm.valid_to || null,
        is_active: promotionForm.is_active,
      }),
    onSuccess: async () => {
      toast.success("Promoción creada");
      setPromotionForm((current) => ({ ...current, name: "", qty_required: "", discount_percent: "", unit_price: "", box_price: "" }));
      await refreshDetail();
    },
  });

  const mediaMutation = useMutation({
    mutationFn: async () => {
      if (!mediaFile) {
        throw new Error("Selecciona un archivo");
      }
      return uploadProductMedia(productId!, { media_type: mediaType, is_primary: false, file: mediaFile });
    },
    onSuccess: async () => {
      toast.success("Media subida");
      setMediaFile(null);
      await refreshDetail();
    },
  });

  const activeAdr = detailQuery.data?.adr_configs.find((item) => item.valid_to === null) ?? null;

  async function submitMutation(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo completar la operación.");
    }
  }

  if (!productId) {
    return <ProductosSection title="Detalle producto" description="Falta productId."> </ProductosSection>;
  }

  return (
    <ProductosSection
      title={detailQuery.data?.name ?? "Detalle producto"}
      description="Gestión operativa de barcodes, precios, costos, impuestos, ADR, media y promociones."
      actions={
        <div className="flex gap-2">
          <Link to={`/app/productos/${productId}`}>
            <Button variant="secondary">Editar ficha</Button>
          </Link>
          <div className="flex items-center gap-2">
            <Switch
              checked={detailQuery.data?.is_active ?? true}
              onChange={(event) => submitMutation(() => toggleProduct(productId, event.target.checked, "Cambio manual"))}
            />
            <span className="text-sm text-muted-foreground">{detailQuery.data?.is_active ? "Activo" : "Inactivo"}</span>
          </div>
        </div>
      }
    >
      {error ? <Alert title="Operación fallida">{error}</Alert> : null}
      {detailQuery.error ? <Alert title="No se pudo cargar el producto">{detailQuery.error.message}</Alert> : null}

      <Card>
        <CardHeader>
          <CardTitle>Resumen</CardTitle>
          <CardDescription>{detailQuery.data ? `${detailQuery.data.sku} · ${detailQuery.data.condition_code}` : "Cargando..."}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3 text-sm text-foreground">
          <div><span className="text-muted-foreground">Estado:</span> {detailQuery.data?.status_code ?? "-"}</div>
          <div><span className="text-muted-foreground">Activo:</span> {detailQuery.data?.is_active ? "Sí" : "No"}</div>
          <div><span className="text-muted-foreground">Unidad:</span> {detailQuery.data?.unit_id ?? "-"}</div>
          <div><span className="text-muted-foreground">Marca:</span> {detailQuery.data?.brand_id ?? "-"}</div>
          <div><span className="text-muted-foreground">Grupo:</span> {detailQuery.data?.group_id ?? "-"}</div>
          <div><span className="text-muted-foreground">Subcategoría:</span> {detailQuery.data?.subcategory_id ?? "-"}</div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Barcodes</CardTitle>
            <CardDescription>Un solo barcode puede ser principal.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[180px_1fr_auto]">
              <select className={selectClassName} value={barcodeType} onChange={(event) => setBarcodeType(event.target.value)}>
                <option value="INTERNAL">INTERNAL</option>
                <option value="CABYS">CABYS</option>
                <option value="MATRICULA">MATRICULA</option>
                <option value="GS1">GS1</option>
              </select>
              <Input value={barcodeValue} onChange={(event) => setBarcodeValue(event.target.value)} placeholder="Código" />
              <Button onClick={() => submitMutation(() => barcodeMutation.mutateAsync())}>Agregar</Button>
            </div>
            <DataTable
              columns={[
                { key: "type", header: "Tipo", render: (row) => row.barcode_type },
                { key: "value", header: "Código", render: (row) => row.barcode },
                { key: "primary", header: "Principal", render: (row) => (row.is_primary ? "Sí" : "No") },
                {
                  key: "actions",
                  header: "Acciones",
                  render: (row) => (
                    <DropdownMenu
                      align="end"
                      trigger={<Button variant="secondary" className="h-7 w-7 px-0 py-0">⋮</Button>}
                      items={[
                        ...(!row.is_primary
                          ? [{ label: "Marcar principal", onClick: () => submitMutation(() => setPrimaryProductBarcode(productId, row.id)) } as DropdownItem]
                          : []),
                        { label: "Eliminar", destructive: true, onClick: () => setConfirmDelete({ id: row.id, onConfirm: () => submitMutation(() => deleteProductBarcode(productId, row.id)) }) },
                      ]}
                    />
                  ),
                },
              ]}
              rows={detailQuery.data?.barcodes ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin barcodes."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Precios</CardTitle>
            <CardDescription>Nueva fila = nueva vigencia.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[180px_1fr_120px_auto]">
              <select className={selectClassName} value={priceList} onChange={(event) => setPriceList(event.target.value)}>
                <option value="UNITARIO">UNITARIO</option>
                <option value="INTERMEDIO">INTERMEDIO</option>
                <option value="CAJA">CAJA</option>
                <option value="LISTA2">LISTA2</option>
                <option value="LISTA3">LISTA3</option>
                <option value="LISTA4">LISTA4</option>
              </select>
              <Input type="number" value={priceAmount} onChange={(event) => setPriceAmount(event.target.value)} placeholder="Monto" />
              <Input value={priceCurrency} onChange={(event) => setPriceCurrency(event.target.value.toUpperCase())} placeholder="MON" />
              <Button onClick={() => submitMutation(() => priceMutation.mutateAsync())}>Agregar</Button>
            </div>
            <DataTable
              columns={[
                { key: "list", header: "Lista", render: (row) => row.price_list },
                { key: "amount", header: "Monto", render: (row) => `${row.amount} ${row.currency}` },
                { key: "from", header: "Desde", render: (row) => row.valid_from },
                { key: "to", header: "Hasta", render: (row) => row.valid_to ?? "Vigente" },
              ]}
              rows={detailQuery.data?.prices ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin precios."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Costos</CardTitle>
            <CardDescription>Nueva fila = nueva vigencia.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[180px_1fr_120px_auto]">
              <select className={selectClassName} value={costType} onChange={(event) => setCostType(event.target.value)}>
                <option value="ACTUAL">ACTUAL</option>
                <option value="REPOSICION">REPOSICION</option>
                <option value="ANTERIOR">ANTERIOR</option>
                <option value="CGI">CGI</option>
                <option value="TOTAL">TOTAL</option>
              </select>
              <Input type="number" value={costAmount} onChange={(event) => setCostAmount(event.target.value)} placeholder="Monto" />
              <Input value={costCurrency} onChange={(event) => setCostCurrency(event.target.value.toUpperCase())} placeholder="MON" />
              <Button onClick={() => submitMutation(() => costMutation.mutateAsync())}>Agregar</Button>
            </div>
            <DataTable
              columns={[
                { key: "type", header: "Tipo", render: (row) => row.cost_type },
                { key: "amount", header: "Monto", render: (row) => `${row.amount} ${row.currency}` },
                { key: "from", header: "Desde", render: (row) => row.valid_from },
                { key: "to", header: "Hasta", render: (row) => row.valid_to ?? "Vigente" },
              ]}
              rows={detailQuery.data?.costs ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin costos."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Impuestos</CardTitle>
            <CardDescription>Reemplaza la configuración vigente por tipo.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-foreground">
            <label className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2">
              <Checkbox checked={taxValues.igv_exempt} onChange={(event) => setTaxValues((current) => ({ ...current, igv_exempt: event.target.checked }))} />
              IGV exonerado
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span>Percepción</span>
                <Input value={taxValues.percepcion} onChange={(event) => setTaxValues((current) => ({ ...current, percepcion: event.target.value }))} placeholder={currentTaxes.percepcion?.value?.toString() ?? "0"} />
              </label>
              <label className="block space-y-2">
                <span>Comisión externa</span>
                <Input value={taxValues.comision_ext} onChange={(event) => setTaxValues((current) => ({ ...current, comision_ext: event.target.value }))} placeholder={currentTaxes.comision?.value?.toString() ?? "0"} />
              </label>
            </div>
            <Button onClick={() => submitMutation(() => taxMutation.mutateAsync())}>Guardar impuestos</Button>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>ADR</CardTitle>
            <CardDescription>La configuración activa del producto transportado vive aquí, no en logística.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <DataTable
              columns={[
                { key: "category", header: "Categoría", render: (row: ProductAdr) => row.category ?? "-" },
                { key: "un", header: "UN", render: (row: ProductAdr) => row.un_number ?? "-" },
                { key: "label", header: "Etiqueta", render: (row: ProductAdr) => row.label ?? "-" },
                { key: "from", header: "Desde", render: (row: ProductAdr) => row.valid_from },
                { key: "to", header: "Hasta", render: (row: ProductAdr) => row.valid_to ?? "Vigente" },
              ]}
              rows={detailQuery.data?.adr_configs ?? []}
              rowKey={(row) => row.id}
              onRowClick={(row) => { setEditAdr(row); setIsEditAdrOpen(true); }}
              emptyMessage="Sin configuración ADR."
            />
          </CardContent>
        </Card>

        <Dialog
          open={isEditAdrOpen}
          title="Editar ADR"
          onClose={() => { setIsEditAdrOpen(false); setEditAdr(null); }}
          maxWidthClassName="max-w-2xl"
        >
          {editAdr ? (
            <div className="space-y-4">
              <div className="rounded-md border border-border bg-muted/40 p-3 space-y-3">
                <p className="text-sm font-medium text-foreground">Receta criogénica</p>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Fuente 1</span>
                    <Input value={editAdr.source_product_id ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, source_product_id: event.target.value || null } : null)} placeholder="ID criogénico" />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Fuente 2</span>
                    <Input value={editAdr.source_product_id_2 ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, source_product_id_2: event.target.value || null } : null)} placeholder="ID criogénico" />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Fuente 3</span>
                    <Input value={editAdr.source_product_id_3 ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, source_product_id_3: event.target.value || null } : null)} placeholder="ID criogénico" />
                  </label>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-4">
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Categoría</span>
                  <Input value={editAdr.category ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, category: event.target.value || null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Tipo bulto</span>
                  <Input value={editAdr.packaging_type ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, packaging_type: event.target.value || null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>UN</span>
                  <Input value={editAdr.un_number ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, un_number: event.target.value || null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Etiqueta</span>
                  <Input value={editAdr.label ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, label: event.target.value || null } : null)} />
                </label>
              </div>
              <div className="grid gap-4 md:grid-cols-4">
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Peso kg</span>
                  <Input value={editAdr.net_weight_kg?.toString() ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, net_weight_kg: event.target.value ? Number(event.target.value) : null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Volumen m3</span>
                  <Input value={editAdr.net_volume_m3?.toString() ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, net_volume_m3: event.target.value ? Number(event.target.value) : null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Factor</span>
                  <Input value={editAdr.factor?.toString() ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, factor: event.target.value ? Number(event.target.value) : null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Puntos</span>
                  <Input value={editAdr.points?.toString() ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, points: event.target.value ? Number(event.target.value) : null } : null)} />
                </label>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Túnel</span>
                  <Input value={editAdr.tunnel_restriction ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, tunnel_restriction: event.target.value || null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Unidad medida</span>
                  <Input value={editAdr.unit_measure ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, unit_measure: event.target.value || null } : null)} />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Sublínea ADR</span>
                  <select className={selectClassName} value={editAdr.subline_id ?? ""} onChange={(event) => setEditAdr((current) => current ? { ...current, subline_id: event.target.value || null } : null)}>
                    <option value="">Sin sublínea ADR</option>
                    {(sublineQuery.data ?? []).map((item) => (
                      <option key={item.id} value={item.id}>{item.name}</option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Mercancía / descripción</span>
                <Textarea
                  className="min-h-20"
                  value={editAdr.cargo_description ?? ""}
                  onChange={(event) => setEditAdr((current) => current ? { ...current, cargo_description: event.target.value || null } : null)}
                />
              </label>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => { setIsEditAdrOpen(false); setEditAdr(null); }}>
                  Cancelar
                </Button>
                <Button type="button" onClick={() => updateAdrMutation.mutateAsync()} disabled={updateAdrMutation.isPending}>
                  {updateAdrMutation.isPending ? "Guardando..." : "Guardar"}
                </Button>
              </div>
            </div>
          ) : null}
        </Dialog>

        <Card>
          <CardHeader>
            <CardTitle>Media</CardTitle>
            <CardDescription>Archivos locales preparados para evolucionar a R2.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[180px_1fr_auto]">
              <select className={selectClassName} value={mediaType} onChange={(event) => setMediaType(event.target.value)}>
                <option value="PHOTO">PHOTO</option>
                <option value="BARCODE_IMAGE">BARCODE_IMAGE</option>
                <option value="DOC">DOC</option>
              </select>
              <input
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
                type="file"
                onChange={(event: ChangeEvent<HTMLInputElement>) => setMediaFile(event.target.files?.[0] ?? null)}
              />
              <Button onClick={() => submitMutation(() => mediaMutation.mutateAsync())}>Subir</Button>
            </div>
            <DataTable
              columns={[
                { key: "type", header: "Tipo", render: (row) => row.media_type },
                { key: "url", header: "Archivo", render: (row) => <a className="text-cyan-300 hover:underline" href={row.url} target="_blank" rel="noreferrer">Abrir</a> },
                { key: "primary", header: "Principal", render: (row) => (row.is_primary ? "Sí" : "No") },
                {
                  key: "actions",
                  header: "Acciones",
                  render: (row) => (
                    <DropdownMenu
                      align="end"
                      trigger={<Button variant="secondary" className="h-7 w-7 px-0 py-0">⋮</Button>}
                      items={[
                        ...(!row.is_primary
                          ? [{ label: "Marcar principal", onClick: () => submitMutation(() => setPrimaryProductMedia(productId, row.id)) } as DropdownItem]
                          : []),
                        { label: "Eliminar", destructive: true, onClick: () => setConfirmDelete({ id: row.id, onConfirm: () => submitMutation(() => deleteProductMedia(productId, row.id)) }) },
                      ]}
                    />
                  ),
                },
              ]}
              rows={detailQuery.data?.media_items ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin media."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Promociones</CardTitle>
            <CardDescription>Promociones simples por producto.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <Input value={promotionForm.name} onChange={(event) => setPromotionForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nombre" />
              <select className={selectClassName} value={promotionForm.condition} onChange={(event) => setPromotionForm((current) => ({ ...current, condition: event.target.value }))}>
                <option value="PORCENTAJE">PORCENTAJE</option>
                <option value="CANTIDAD">CANTIDAD</option>
                <option value="OFERTA">OFERTA</option>
              </select>
              <Input value={promotionForm.qty_required} onChange={(event) => setPromotionForm((current) => ({ ...current, qty_required: event.target.value }))} placeholder="Cantidad requerida" />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <Input value={promotionForm.discount_percent} onChange={(event) => setPromotionForm((current) => ({ ...current, discount_percent: event.target.value }))} placeholder="% descuento" />
              <Input value={promotionForm.unit_price} onChange={(event) => setPromotionForm((current) => ({ ...current, unit_price: event.target.value }))} placeholder="Precio unitario" />
              <Input value={promotionForm.box_price} onChange={(event) => setPromotionForm((current) => ({ ...current, box_price: event.target.value }))} placeholder="Precio caja" />
            </div>
            <Button onClick={() => submitMutation(() => promotionMutation.mutateAsync())}>Crear promoción</Button>
            <DataTable
              columns={[
                { key: "name", header: "Nombre", render: (row) => row.name ?? "-" },
                { key: "condition", header: "Tipo", render: (row) => row.condition },
                { key: "discount", header: "Descuento", render: (row) => row.discount_percent ?? "-" },
                { key: "validity", header: "Vigencia", render: (row) => `${row.valid_from} → ${row.valid_to ?? "vigente"}` },
                {
                  key: "actions",
                  header: "Acciones",
                  render: (row) => (
                    <Button variant="secondary" onClick={() => setConfirmDelete({ id: row.id, onConfirm: () => submitMutation(() => deletePromotion(row.id)) })}>
                      Eliminar
                    </Button>
                  ),
                },
              ]}
              rows={detailQuery.data?.promotions ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin promociones."
            />
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => {
          confirmDelete?.onConfirm();
          setConfirmDelete(null);
        }}
        title="Confirmar eliminación"
        description="¿Estás seguro de eliminar este elemento?"
        destructive
        confirmLabel="Eliminar"
      />
    </ProductosSection>
  );
}
