import { Checkbox, Input, Switch } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { Field, FormRow } from "../utils/formatters";
import type { CylinderFormState } from "./cylinder-form-state";

type CylinderFormFieldsProps = {
  form: CylinderFormState;
  gasProducts: Array<{ id: string; name: string; content_kg?: number | null }>;
  brands: Array<{ id: string; name: string }>;
  conditions: Array<{ code: string; name: string }>;
  includeActivation: boolean;
  onChange: (next: CylinderFormState) => void;
};

export function CylinderFormFields({
  form,
  gasProducts,
  brands,
  conditions,
  includeActivation,
  onChange,
}: CylinderFormFieldsProps) {
  function updateField<Key extends keyof CylinderFormState>(key: Key, value: CylinderFormState[Key]) {
    onChange({ ...form, [key]: value });
  }

  return (
    <div className="space-y-4">
      <FormRow title="Identificación">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Serial"><Input value={form.serial} onChange={(event) => { updateField("serial", event.target.value); if (!form.barcode2) { updateField("barcode2", event.target.value); } }} /></Field>
        <Field className="col-span-full md:col-span-4 xl:col-span-4" label="Descripción"><Input value={form.description} onChange={(event) => updateField("description", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-4 xl:col-span-4" label="Ubicación"><Input value={form.location} onChange={(event) => updateField("location", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-2 xl:col-span-2" label="Caja / lote"><Input value={form.box_number} onChange={(event) => updateField("box_number", event.target.value)} /></Field>
      </div>
      </FormRow>

      <FormRow title="Códigos y Clasificación">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6 xl:grid-cols-12">
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Matrícula etiqueta"><Input value={form.barcode2} onChange={(event) => updateField("barcode2", event.target.value)} /></Field>
        <Field className="col-span-full md:col-span-3 xl:col-span-3" label="Gas">
          <Select
            value={form.gas_group_id}
            onChange={(value) => {
              updateField("gas_group_id", value);
              const product = gasProducts.find((p) => p.id === value);
              if (product?.content_kg) {
                if (!form.weight_origin) {
                  updateField("weight_origin", product.content_kg.toString());
                }
                if (!form.content_kg) {
                  updateField("content_kg", product.content_kg.toString());
                }
              }
            }}
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
          <Checkbox checked={form.is_service} onChange={(event) => updateField("is_service", event.target.checked)} />
          Producto de servicio
        </label>
      </Field>
      <Field className="col-span-full md:col-span-6 xl:col-span-5" label="Uso medicinal">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <Checkbox checked={form.is_medical} onChange={(event) => updateField("is_medical", event.target.checked)} />
          Envase para uso medicinal
        </label>
      </Field>
      {form.is_medical ? (
        <Field className="col-span-full" label="Notas medicinales">
          <Input value={form.medical_notes} onChange={(event) => updateField("medical_notes", event.target.value)} placeholder="Ej: Oxígeno medicinal USP, lote..." />
        </Field>
      ) : null}
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

      {includeActivation ? (
        <Field label="Activo">
          <div className="flex items-center gap-2 text-sm text-foreground">
            <Switch checked={form.is_active} onChange={(event) => updateField("is_active", event.target.checked)} />
            <span>Envase activo</span>
          </div>
        </Field>
      ) : null}
    </div>
  );
}
