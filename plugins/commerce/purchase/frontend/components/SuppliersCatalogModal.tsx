import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { useMemo, useState } from "react";
import { listSuppliers } from "../api";
import type { Supplier } from "../types";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";
import { Dialog } from "@systutor/shell/ui/dialog";
import { SupplierDetailModal } from "./SupplierDetailModal";
import { SupplierFormModal } from "./SupplierFormModal";

type Props = {
  open: boolean;
  onClose: () => void;
};

/** Catálogo de proveedores en modal: búsqueda + tabla limpia + doble click = detalle. */
export function SuppliersCatalogModal({ open, onClose }: Props) {
  const [search, setSearch] = useState("");
  const [detailId, setDetailId] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);

  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
    enabled: open,
  });

  const suppliers = suppliersQuery.data ?? [];
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return suppliers;
    return suppliers.filter((s) =>
      [s.name, s.commercial_name, s.document_number, s.email, s.phone]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q)),
    );
  }, [suppliers, search]);

  const detailSupplier: Supplier | null =
    suppliers.find((s) => s.id === detailId) ?? null;
  const editSupplier: Supplier | null =
    suppliers.find((s) => s.id === editId) ?? null;

  return (
    <>
      <Dialog
        open={open}
        title="Proveedores"
        description="Doble click sobre un proveedor para ver su detalle completo."
        onClose={onClose}
        maxWidthClassName="max-w-5xl"
      >
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por nombre, documento, email o teléfono"
              className="max-w-sm"
            />
            <Button onClick={() => setFormOpen(true)}>Nuevo proveedor</Button>
          </div>
          <Card>
            <CardContent>
              <DataTable
                columns={[
                  {
                    key: "name",
                    header: "Proveedor",
                    render: (row) => (
                      <div className="space-y-1">
                        <p className="font-medium text-foreground">{row.commercial_name ?? row.name}</p>
                        {row.commercial_name ? (
                          <p className="text-xs text-muted-foreground">Fiscal: {row.name}</p>
                        ) : null}
                      </div>
                    ),
                  },
                  {
                    key: "doc",
                    header: "Documento",
                    render: (row) =>
                      row.document_number ? `${row.document_type_code ?? ""} ${row.document_number}`.trim() : "-",
                  },
                  { key: "email", header: "Email", render: (row) => row.email ?? "-" },
                  { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
                  {
                    key: "status",
                    header: "Estado",
                    render: (row) => (row.is_active ? "Activo" : "Inactivo"),
                  },
                ]}
                rows={filtered}
                rowKey={(row) => row.id}
                onRowDoubleClick={(row) => setDetailId(row.id)}
                emptyMessage="No hay proveedores registrados."
              />
              <p className="mt-3 text-sm text-muted-foreground">
                {suppliersQuery.data
                  ? `${filtered.length} de ${suppliers.length} proveedores`
                  : "Cargando proveedores..."}
              </p>
            </CardContent>
          </Card>
        </div>
      </Dialog>

      <SupplierDetailModal
        open={detailId !== null}
        supplier={detailSupplier}
        onClose={() => setDetailId(null)}
        onEdit={(id) => {
          setDetailId(null);
          setEditId(id);
          setFormOpen(true);
        }}
      />

      <SupplierFormModal
        open={formOpen}
        supplier={editSupplier}
        onClose={() => {
          setFormOpen(false);
          setEditId(null);
        }}
      />
    </>
  );
}
