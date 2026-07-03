import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Field, FormRow } from "../utils/formatters";
import type { CylinderFormState } from "./cylinder-form-state";

type CylinderFormFieldsProps = {
  form: CylinderFormState;
  gasProducts: Array<{ id: string; name: string }>;
  brands: Array<{ id: string; name: string }>;
  adrSublineOptions: Array<{ value: string; label: string }>;
  conditions: Array<{ code: string; name: string }>;
  includeActivation: boolean;
  onChange: (next: CylinderFormState) => void;
};

export function CylinderFormFields({
  form,
  gasProducts,
  brands,
  adrSublineOptions,
  conditions,
  includeActivation,
  onChange,
}: CylinderFormFieldsProps) {
  function updateField<Key extends keyof CylinderFormState>(key: Key, value: CylinderFormState[Key]) {
    onChange({ ...form, [key]: value });
  }

  const sublineOptions = form.adr_subline && !adrSublineOptions.some((item) => item.value === form.adr_subline)
    ? [{ value: form.adr_subline, label: `${form.adr_subline} (actual)` }, ...adrSublineOptions]
    : adrSublineOptions;

  return (
    <div className="space-y-4">
      <FormRow title="Identificación">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Serial"><Input value={form.serial} onChange={(event) => updateField("serial", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-4 xl:col-span-4" label="Descripción"><Input value={form.description} onChange={(event) => updateField("description", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-4 xl:col-span-4" label="Ubicación"><Input value={form.location} onChange={(event) => updateField("location", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Caja / lote"><Input value={form.box_number} onChange={(event) => updateField("box_number", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="Códigos y Clasificación">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Barcode producto"><Input value={form.barcode1} onChange={(event) => updateField("barcode1", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Matrícula etiqueta"><Input value={form.barcode2} onChange={(event) => updateField("barcode2", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Gas">
          <Select
            value={form.gas_group_id}
            onChange={(value) => updateField("gas_group_id", value)}
            placeholder="Sin asignar"
            options={gasProducts.map((item) => ({ value: item.id, label: item.name }))}
          />
        </Field>
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Marca">
          <Select
            value={form.brand_id}
            onChange={(value) => updateField("brand_id", value)}
            placeholder="Sin asignar"
            options={brands.map((item) => ({ value: item.id, label: item.name }))}
          />
        </Field>
      </div>
      </FormRow>

      <FormRow title="Datos Comerciales y Uso">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Condición">
        <Select value={form.condition} onChange={(value) => updateField("condition", value)}
          placeholder="Sin asignar"
          options={conditions.map((item) => ({ value: item.code, label: item.name }))} />
      </Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Contenido kg"><Input type="number" value={form.content_kg} onChange={(event) => updateField("content_kg", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Volumen m3"><Input type="number" value={form.volume_m3} onChange={(event) => updateField("volume_m3", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="País"><Input value={form.country_code} onChange={(event) => updateField("country_code", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Costo"><Input type="number" value={form.cost} onChange={(event) => updateField("cost", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Precio"><Input type="number" value={form.price} onChange={(event) => updateField("price", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-6 xl:col-span-5" label="Es servicio">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input type="checkbox" checked={form.is_service} onChange={(event) => updateField("is_service", event.target.checked)} />
          Producto de servicio
        </label>
      </Field>
      </div>
      </FormRow>

      <FormRow title="Fabricación y PH">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Fecha fabricación"><Input type="date" value={form.manufacturer_date} onChange={(event) => updateField("manufacturer_date", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-3" label="Código fabricación"><Input value={form.manufacturer_code} onChange={(event) => updateField("manufacturer_code", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-1" label="Año"><Input type="number" value={form.manufacture_year} onChange={(event) => updateField("manufacture_year", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Peso origen"><Input type="number" value={form.weight_origin} onChange={(event) => updateField("weight_origin", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Peso actual"><Input type="number" value={form.weight_current} onChange={(event) => updateField("weight_current", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Última PH"><Input type="date" value={form.last_hydrotest_date} onChange={(event) => updateField("last_hydrotest_date", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Siguiente PH"><Input type="date" value={form.next_hydrotest_date} onChange={(event) => updateField("next_hydrotest_date", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="ADR">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Categoría"><Input value={form.adr_category} onChange={(event) => updateField("adr_category", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="UN"><Input value={form.adr_un_number} onChange={(event) => updateField("adr_un_number", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Etiqueta"><Input value={form.adr_label} onChange={(event) => updateField("adr_label", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Tipo bulto"><Input value={form.adr_package_type} onChange={(event) => updateField("adr_package_type", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Peso kg"><Input type="number" value={form.adr_weight_kg} onChange={(event) => updateField("adr_weight_kg", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Túnel"><Input value={form.adr_tunnel} onChange={(event) => updateField("adr_tunnel", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Sublínea">
          <Select
            value={form.adr_subline}
            onChange={(value) => updateField("adr_subline", value)}
            placeholder="Sin asignar"
            options={sublineOptions}
          />
        </Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Factor"><Input type="number" value={form.adr_factor} onChange={(event) => updateField("adr_factor", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Puntos"><Input type="number" value={form.adr_points} onChange={(event) => updateField("adr_points", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-1 xl:col-span-1" label="Unidad"><Input value={form.adr_unit_measure} onChange={(event) => updateField("adr_unit_measure", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="Mercancía ADR">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-6 xl:col-span-12" label="Mercancía"><Input value={form.adr_merchandise} onChange={(event) => updateField("adr_merchandise", event.target.value)} /></Field>
      </div>
      </FormRow>
      {includeActivation ? (
        <Field label="Activo">
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input type="checkbox" checked={form.is_active} onChange={(event) => updateField("is_active", event.target.checked)} />
            Envase activo
          </label>
        </Field>
      ) : null}
    </div>
  );
}
