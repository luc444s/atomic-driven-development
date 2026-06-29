import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import {
  createBrand,
  createCategory,
  createGroup,
  createInsumoType,
  createLine,
  createSubcategory,
  createSubline,
  createUnit,
  listBrands,
  listCategories,
  listGroups,
  listInsumoTypes,
  listLines,
  listSubcategories,
  listSubline,
  listUnits,
  productosKeys,
} from "../api";

const selectClassName =
  "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-cyan-500";

type CatalogType = "categories" | "lines" | "subline" | "brands" | "insumo-types" | "units" | "subcategories" | "groups";

const CATALOG_MENU_ITEMS: Array<{ type: CatalogType; label: string; description: string }> = [
  { type: "categories", label: "Categorías", description: "Rubros o categorías superiores." },
  { type: "lines", label: "Líneas", description: "Clasificación principal del producto." },
  { type: "subline", label: "Sublíneas", description: "Detalle de línea para segmentación adicional." },
  { type: "brands", label: "Marcas", description: "Marcas comerciales y técnicas." },
  { type: "insumo-types", label: "Tipos de insumo", description: "Segmentación de insumo según operación." },
  { type: "units", label: "Unidades", description: "Unidad base, m3, litros y kg." },
  { type: "subcategories", label: "Subcategorías", description: "GAS, BOMBONAS, PRODUCTOS, SERVICIOS u otras variantes." },
  { type: "groups", label: "Grupos", description: "Agrupación logística/comercial sin pricing operativo." },
];

const CATALOG_LABELS: Record<CatalogType, string> = {
  categories: "Categorías",
  lines: "Líneas",
  subline: "Sublíneas",
  brands: "Marcas",
  "insumo-types": "Tipos de insumo",
  units: "Unidades",
  subcategories: "Subcategorías",
  groups: "Grupos",
};

export type ModalCatalogoProps = {
  open: boolean;
  onClose: () => void;
  asPage?: boolean;
};

export function ModalCatalogo({ open, onClose, asPage }: ModalCatalogoProps) {
  const [selected, setSelected] = useState<CatalogType | null>(null);

  if (asPage) {
    return <CatalogoMenuContent onSelect={setSelected} />;
  }

  return (
    <>
      <Dialog
        open={open && !selected}
        title="Catálogos base"
        description="Aquí se construye la estructura maestra sobre la que luego operan los productos."
        onClose={onClose}
        maxWidthClassName="max-w-2xl"
      >
        <CatalogoMenuContent onSelect={(type) => setSelected(type)} />
      </Dialog>

      {selected ? (
        <ModalSubCatalogo
          catalogType={selected}
          onBack={() => setSelected(null)}
          onClose={onClose}
        />
      ) : null}
    </>
  );
}

function CatalogoMenuContent({ onSelect }: { onSelect: (type: CatalogType) => void }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {CATALOG_MENU_ITEMS.map((item) => (
        <button
          key={item.type}
          type="button"
          onClick={() => onSelect(item.type)}
          className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-left transition hover:border-cyan-700 hover:bg-slate-900"
        >
          <p className="text-sm font-medium text-slate-200">{item.label}</p>
          <p className="mt-1 text-xs text-slate-500">{item.description}</p>
        </button>
      ))}
    </div>
  );
}

type ModalSubCatalogoProps = {
  catalogType: CatalogType;
  onBack: () => void;
  onClose: () => void;
};

function SimpleSubCatalogForm({
  title,
  queryKey,
  queryFn,
  createFn,
}: {
  title: string;
  queryKey: readonly unknown[];
  queryFn: () => Promise<Array<{ id: string; code: string; name: string; description?: string | null }>>;
  createFn: (payload: { code: string; name: string; description: string | null }) => Promise<unknown>;
}) {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [descriptionValue, setDescriptionValue] = useState("");
  const query = useQuery({ queryKey, queryFn });
  const mutation = useMutation({
    mutationFn: async () => createFn({ code, name, description: descriptionValue || null }),
    onSuccess: async () => {
      setCode("");
      setName("");
      setDescriptionValue("");
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-[120px_1fr_1fr_auto]">
        <Input value={code} onChange={(event) => setCode(event.target.value)} placeholder="Código" />
        <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Nombre" />
        <Input value={descriptionValue} onChange={(event) => setDescriptionValue(event.target.value)} placeholder="Descripción" />
        <Button onClick={() => mutation.mutate()}>Crear</Button>
      </div>
      {query.error ? <Alert title={`No se pudo cargar ${title.toLowerCase()}`}>{query.error.message}</Alert> : null}
      <DataTable
        columns={[
          { key: "code", header: "Código", render: (row) => row.code },
          { key: "name", header: "Nombre", render: (row) => row.name },
          { key: "description", header: "Descripción", render: (row) => row.description ?? "-" },
        ]}
        rows={query.data ?? []}
        rowKey={(row) => row.id}
        emptyMessage="Sin registros."
      />
    </div>
  );
}

function ModalSubCatalogo({ catalogType, onBack, onClose }: ModalSubCatalogoProps) {
  const queryClient = useQueryClient();
  const title = CATALOG_LABELS[catalogType];

  const categoriesQuery = useQuery({ queryKey: productosKeys.catalogs.categories, queryFn: listCategories });
  const linesQuery = useQuery({ queryKey: productosKeys.catalogs.lines, queryFn: listLines });
  const sublineQuery = useQuery({ queryKey: productosKeys.catalogs.subline, queryFn: listSubline });
  const unitsQuery = useQuery({ queryKey: productosKeys.catalogs.units, queryFn: listUnits });
  const groupsQuery = useQuery({ queryKey: productosKeys.catalogs.groups, queryFn: listGroups });

  const [lineForm, setLineForm] = useState({ code: "", name: "", category_id: "", description: "" });
  const [sublineForm, setSublineForm] = useState({ code: "", name: "", line_id: "" });
  const [unitForm, setUnitForm] = useState({ code: "", name: "", equivalencia: "", m3_factor: "", liter_factor: "", kg_factor: "" });
  const [groupForm, setGroupForm] = useState({ code: "", name: "", gas_product_id: "", line_id: "", subline_id: "", unit_id: "" });

  const createLineMutation = useMutation({
    mutationFn: async () => createLine({ ...lineForm, category_id: lineForm.category_id || null, description: lineForm.description || null }),
    onSuccess: async () => {
      setLineForm({ code: "", name: "", category_id: "", description: "" });
      await queryClient.invalidateQueries({ queryKey: productosKeys.catalogs.lines });
    },
  });

  const createSublineMutation = useMutation({
    mutationFn: async () => createSubline(sublineForm),
    onSuccess: async () => {
      setSublineForm({ code: "", name: "", line_id: "" });
      await queryClient.invalidateQueries({ queryKey: productosKeys.catalogs.subline });
    },
  });

  const createUnitMutation = useMutation({
    mutationFn: async () =>
      createUnit({
        code: unitForm.code,
        name: unitForm.name,
        equivalencia: unitForm.equivalencia ? Number(unitForm.equivalencia) : null,
        m3_factor: unitForm.m3_factor ? Number(unitForm.m3_factor) : null,
        liter_factor: unitForm.liter_factor ? Number(unitForm.liter_factor) : null,
        kg_factor: unitForm.kg_factor ? Number(unitForm.kg_factor) : null,
      }),
    onSuccess: async () => {
      setUnitForm({ code: "", name: "", equivalencia: "", m3_factor: "", liter_factor: "", kg_factor: "" });
      await queryClient.invalidateQueries({ queryKey: productosKeys.catalogs.units });
    },
  });

  const createGroupMutation = useMutation({
    mutationFn: async () =>
      createGroup({
        code: groupForm.code,
        name: groupForm.name,
        gas_product_id: groupForm.gas_product_id || null,
        line_id: groupForm.line_id || null,
        subline_id: groupForm.subline_id || null,
        unit_id: groupForm.unit_id || null,
      }),
    onSuccess: async () => {
      setGroupForm({ code: "", name: "", gas_product_id: "", line_id: "", subline_id: "", unit_id: "" });
      await queryClient.invalidateQueries({ queryKey: productosKeys.catalogs.groups });
    },
  });

  function renderContent() {
    switch (catalogType) {
      case "categories":
        return (
          <SimpleSubCatalogForm
            title="Categorías"
            queryKey={productosKeys.catalogs.categories}
            queryFn={listCategories}
            createFn={createCategory}
          />
        );
      case "lines":
        return (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[120px_1fr_1fr_1fr_auto]">
              <Input value={lineForm.code} onChange={(event) => setLineForm((current) => ({ ...current, code: event.target.value }))} placeholder="Código" />
              <Input value={lineForm.name} onChange={(event) => setLineForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nombre" />
              <select className={selectClassName} value={lineForm.category_id} onChange={(event) => setLineForm((current) => ({ ...current, category_id: event.target.value }))}>
                <option value="">Sin categoría</option>
                {(categoriesQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              <Input value={lineForm.description} onChange={(event) => setLineForm((current) => ({ ...current, description: event.target.value }))} placeholder="Descripción" />
              <Button onClick={() => createLineMutation.mutate()}>Crear</Button>
            </div>
            <DataTable
              columns={[
                { key: "code", header: "Código", render: (row) => row.code },
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "category", header: "Categoría", render: (row) => row.category_id ?? "-" },
              ]}
              rows={linesQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin líneas."
            />
          </div>
        );
      case "subline":
        return (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[120px_1fr_1fr_auto]">
              <Input value={sublineForm.code} onChange={(event) => setSublineForm((current) => ({ ...current, code: event.target.value }))} placeholder="Código" />
              <Input value={sublineForm.name} onChange={(event) => setSublineForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nombre" />
              <select className={selectClassName} value={sublineForm.line_id} onChange={(event) => setSublineForm((current) => ({ ...current, line_id: event.target.value }))}>
                <option value="">Selecciona línea</option>
                {(linesQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              <Button onClick={() => createSublineMutation.mutate()}>Crear</Button>
            </div>
            <DataTable
              columns={[
                { key: "code", header: "Código", render: (row) => row.code },
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "line", header: "Línea", render: (row) => row.line_id },
              ]}
              rows={sublineQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin sublíneas."
            />
          </div>
        );
      case "brands":
        return (
          <SimpleSubCatalogForm
            title="Marcas"
            queryKey={productosKeys.catalogs.brands}
            queryFn={listBrands}
            createFn={createBrand}
          />
        );
      case "insumo-types":
        return (
          <SimpleSubCatalogForm
            title="Tipos de insumo"
            queryKey={productosKeys.catalogs.insumoTypes}
            queryFn={listInsumoTypes}
            createFn={createInsumoType}
          />
        );
      case "units":
        return (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Input value={unitForm.code} onChange={(event) => setUnitForm((current) => ({ ...current, code: event.target.value }))} placeholder="Código" />
              <Input value={unitForm.name} onChange={(event) => setUnitForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nombre" />
              <Input value={unitForm.equivalencia} onChange={(event) => setUnitForm((current) => ({ ...current, equivalencia: event.target.value }))} placeholder="Equivalencia" />
              <Input value={unitForm.m3_factor} onChange={(event) => setUnitForm((current) => ({ ...current, m3_factor: event.target.value }))} placeholder="Factor m3" />
              <Input value={unitForm.liter_factor} onChange={(event) => setUnitForm((current) => ({ ...current, liter_factor: event.target.value }))} placeholder="Factor litros" />
              <Input value={unitForm.kg_factor} onChange={(event) => setUnitForm((current) => ({ ...current, kg_factor: event.target.value }))} placeholder="Factor kg" />
            </div>
            <Button onClick={() => createUnitMutation.mutate()}>Crear unidad</Button>
            <DataTable
              columns={[
                { key: "code", header: "Código", render: (row) => row.code },
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "eq", header: "Eq", render: (row) => row.equivalencia ?? "-" },
              ]}
              rows={unitsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin unidades."
            />
          </div>
        );
      case "subcategories":
        return (
          <SimpleSubCatalogForm
            title="Subcategorías"
            queryKey={productosKeys.catalogs.subcategories}
            queryFn={listSubcategories}
            createFn={createSubcategory}
          />
        );
      case "groups":
        return (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Input value={groupForm.code} onChange={(event) => setGroupForm((current) => ({ ...current, code: event.target.value }))} placeholder="Código" />
              <Input value={groupForm.name} onChange={(event) => setGroupForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nombre" />
              <select className={selectClassName} value={groupForm.line_id} onChange={(event) => setGroupForm((current) => ({ ...current, line_id: event.target.value }))}>
                <option value="">Sin línea</option>
                {(linesQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              <select className={selectClassName} value={groupForm.subline_id} onChange={(event) => setGroupForm((current) => ({ ...current, subline_id: event.target.value }))}>
                <option value="">Sin sublínea</option>
                {(sublineQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              <select className={selectClassName} value={groupForm.unit_id} onChange={(event) => setGroupForm((current) => ({ ...current, unit_id: event.target.value }))}>
                <option value="">Sin unidad</option>
                {(unitsQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              <Input value={groupForm.gas_product_id} onChange={(event) => setGroupForm((current) => ({ ...current, gas_product_id: event.target.value }))} placeholder="Gas product id opcional" />
            </div>
            <Button onClick={() => createGroupMutation.mutate()}>Crear grupo</Button>
            <DataTable
              columns={[
                { key: "code", header: "Código", render: (row) => row.code },
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "line", header: "Línea", render: (row) => row.line_id ?? "-" },
                { key: "unit", header: "Unidad", render: (row) => row.unit_id ?? "-" },
              ]}
              rows={groupsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin grupos."
            />
          </div>
        );
    }
  }

  return (
    <Dialog
      open
      title={title}
      onClose={() => { onBack(); onClose(); }}
      maxWidthClassName="max-w-3xl"
    >
      <div className="max-h-[75vh] overflow-y-auto space-y-4">
        <Button variant="secondary" onClick={onBack}>← Volver al menú</Button>
        {renderContent()}
      </div>
    </Dialog>
  );
}
