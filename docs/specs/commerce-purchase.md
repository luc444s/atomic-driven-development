# Spec: Módulo Purchase (`plugins/commerce/purchase/`)

**Estado**: `vigente`  
**Plugin ID**: `compras`  
**Versión**: `0.1.0`  
**Fecha**: 2026-08-08

## 1. Alcance

Módulo de compras dentro de Gestión Comercial. Permite crear órdenes de compra a proveedores, recepcionar mercadería contra almacenes, e integrar automáticamente con el módulo de stock vía REST.

## 2. Riesgos

| Riesgo | Mitigación |
|---|---|
| Llamadas HTTP inter-plugin fallan | Idempotencia vía `idempotency_key`, rechaza duplicados |
| Token interno expuesto | Variable de entorno, nunca en código |
| Recepción duplicada de mismo item | `idempotency_key` único por item + order, stock backend devuelve 409 |
| Proveedor dado de baja en medio de orden | Soft-delete con `is_active`, órdenes existentes no se afectan |

## 3. Arquitectura

```
plugins/commerce/
├── plugin.json                          ← id: "compras", entrypoint: purchase.backend.plugin:register
├── _shared/
│   ├── __init__.py
│   └── stock_connector.py               ← cliente REST unico para todos los submodulos de commerce
└── purchase/
    ├── backend/
    │   ├── __init__.py
    │   ├── plugin.py                    ← register(context): router + permissions + events
    │   ├── models.py                    ← ComSupplier, ComPurchaseOrder, ComPurchaseItem, ComPurchaseReceipt
    │   ├── schemas.py                   ← Pydantic create/update/read
    │   ├── router.py                    ← FastAPI endpoints
    │   └── services/
    │       ├── __init__.py
    │       ├── suppliers.py
    │       ├── orders.py
    │       └── receipts.py              ← lógica de recepcion + dispatch a stock via commerce._shared.stock_connector
    ├── frontend/
    │   ├── register.ts
    │   ├── api.ts
    │   ├── types.ts
    │   ├── pages/
    │   │   └── PurchaseOrdersPage.tsx
    │   ├── components/
    │   │   ├── CreateOrderDialog.tsx
    │   │   ├── ReceiveOrderDialog.tsx
    │   │   └── SupplierDialog.tsx
    │   └── forms/
    │       └── purchase-form-state.ts
    └── README.md
```

**`_shared/stock_connector.py`**: único punto de contacto REST con el plugin stock. Futuros submódulos (`sales/`, `invoices/`) lo importan sin duplicar HTTP, tokens ni error handling.

## 4. Dependencias

```json
{
  "requires": ["productos", "stock", "logistics"]
}
```

- `productos` — catálogo de productos para items de orden
- `stock` — API REST `POST /stock/purchase-in` para ingreso de mercadería
- `logistics` — tabla `lg_warehouses` para elegir almacén de recepción

## 5. Modelos

### `com_suppliers`

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| tenant_id | FK tenants | NOT NULL, INDEX |
| name | String(200) | razón social, NOT NULL |
| document_type_code | FK crm_document_types (nullable) | INDEX |
| document_number | String(30) (nullable) | |
| email | String(100) (nullable) | |
| phone | String(50) (nullable) | |
| address | String(300) (nullable) | |
| notes | Text (nullable) | |
| is_active | Boolean, default True | soft-delete |
| created_at | DateTime | |
| updated_at | DateTime | |

### `com_purchase_orders`

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| tenant_id | FK tenants | NOT NULL, INDEX |
| branch_id | FK branches (nullable) | INDEX |
| supplier_id | FK com_suppliers | NOT NULL, INDEX |
| status | String(20) | DRAFT / ORDERED / PARTIAL / RECEIVED / CANCELLED |
| order_date | Date | NOT NULL |
| expected_date | Date (nullable) | |
| notes | Text (nullable) | |
| created_by | FK users | NOT NULL, INDEX |
| created_at | DateTime | |
| updated_at | DateTime | |

### `com_purchase_items`

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| order_id | FK com_purchase_orders ON DELETE CASCADE | NOT NULL, INDEX |
| product_id | FK prod_products | NOT NULL, INDEX |
| quantity | Numeric(10,2) | NOT NULL, >0 |
| unit_cost | Numeric(10,2) | NOT NULL, >0 |
| received_qty | Numeric(10,2), default 0 | >=0, <=quantity |

### `com_purchase_receipts`

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| order_id | FK com_purchase_orders | NOT NULL, INDEX |
| warehouse_id | FK lg_warehouses | NOT NULL, INDEX |
| receipt_date | Date | NOT NULL |
| notes | Text (nullable) | |
| created_by | FK users | NOT NULL, INDEX |
| created_at | DateTime | |

## 6. Permisos

```
compras.supplier.read        — ver lista de proveedores
compras.supplier.manage      — crear, editar, desactivar proveedor
compras.order.read           — ver órdenes y detalle
compras.order.create         — crear orden (DRAFT)
compras.order.manage         — editar (DRAFT), confirmar, cancelar
compras.order.receive        — recepcionar items + integración stock
```

## 7. Endpoints

| Método | Path | Permiso | Request Body | Response |
|---|---|---|---|---|
| GET | `/purchase/suppliers` | supplier.read | query: search, is_active, limit, offset | `list[SupplierRead]` |
| POST | `/purchase/suppliers` | supplier.manage | `SupplierCreateRequest` | `SupplierRead` (201) |
| PATCH | `/purchase/suppliers/{id}` | supplier.manage | `SupplierUpdateRequest` | `SupplierRead` |
| POST | `/purchase/suppliers/{id}/disable` | supplier.manage | — | `SupplierRead` |
| GET | `/purchase/orders` | order.read | query: status, supplier_id, page, limit | `PurchaseOrderPageRead` |
| POST | `/purchase/orders` | order.create | `PurchaseOrderCreateRequest` | `PurchaseOrderRead` (201) |
| GET | `/purchase/orders/{id}` | order.read | — | `PurchaseOrderDetailRead` |
| PATCH | `/purchase/orders/{id}` | order.manage | `PurchaseOrderUpdateRequest` | `PurchaseOrderRead` |
| POST | `/purchase/orders/{id}/confirm` | order.manage | — | `PurchaseOrderRead` |
| POST | `/purchase/orders/{id}/cancel` | order.manage | `{ reason: str? }` | `PurchaseOrderRead` |
| POST | `/purchase/orders/{id}/receive` | order.receive | `ReceiveOrderRequest` | `PurchaseOrderRead` |

### `ReceiveOrderRequest`

```json
{
  "warehouse_id": "uuid",
  "items": [
    {"purchase_item_id": "uuid", "quantity": 5.0},
    {"purchase_item_id": "uuid", "quantity": 10.0}
  ],
  "notes": "Recepción parcial del envío"
}
```

### Schemas

**`SupplierCreateRequest`**: name (req), document_type_code, document_number, email, phone, address, notes

**`SupplierUpdateRequest`**: todos opcionales

**`PurchaseOrderCreateRequest`**: supplier_id (req), items (req, min 1), expected_date, notes  
Cada item: product_id (req), quantity (req, >0), unit_cost (req, >0)

**`PurchaseOrderUpdateRequest`**: expected_date, notes, items (reemplaza todos)

**`PurchaseOrderRead`**: id, supplier (nested), status, order_date, expected_date, notes, items (con received_qty), receipts, created_at

**`PurchaseOrderPageRead`**: items (list), total, limit, offset

## 8. Integración Stock

### StockConnector (shared)

```python
# plugins/commerce/_shared/stock_connector.py
"""Cliente REST unico para el plugin stock. Reutilizado por todos los submodulos de commerce."""

import httpx
from apps.api.app.core.config import Settings


class StockConnector:
    def __init__(self, settings: Settings):
        self.base_url = "http://localhost:8000/api/v1/plugins/stock"
        self.token = settings.internal_api_token

    def purchase_in(self, *, product_id, warehouse_id, quantity,
                    unit_cost, reference_type, reference_id, idempotency_key):
        response = httpx.post(
            f"{self.base_url}/purchase-in",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "idempotency_key": idempotency_key,
            },
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10,
        )
        if response.status_code == 409:
            raise DuplicateReceiptError(
                f"Item {product_id} ya fue recepcionado para esta orden"
            )
        response.raise_for_status()
        return response.json()
```

### Uso desde purchase

```python
# plugins/commerce/purchase/backend/services/receipts.py
from commerce._shared.stock_connector import StockConnector

connector = StockConnector(settings)

for item in items:
    connector.purchase_in(
        product_id=item.product_id,
        warehouse_id=warehouse_id,
        quantity=item.quantity,
        unit_cost=item.unit_cost,
        reference_type="purchase_order",
        reference_id=order_id,
        idempotency_key=f"compras-{order_id}-{item.id}",
    )
```

### Configuración

```bash
# .env
SYSTUTOR_INTERNAL_API_TOKEN=change-me-in-production
```

### Formato idempotency_key

```
"compras-{order_id}-{purchase_item_id}"
```

Garantiza que cada item de orden se recibe exactamente una vez. Si el stock backend ya procesó esa key, devuelve 409 Conflict.

## 9. Máquina de estados

```
[DRAFT] ──confirm──→ [ORDERED]
   │                    │
   │                    ├──receive(total)──→ [RECEIVED]
   │                    │
   │                    ├──receive(partial)─→ [PARTIAL] ──receive(total)─→ [RECEIVED]
   │                    │
   │                    └──cancel──→ [CANCELLED]
   │
   └──cancel──→ [CANCELLED]
```

Reglas de transición:

| Desde | Hacia | Condición |
|---|---|---|
| DRAFT | ORDERED | confirm() |
| DRAFT | CANCELLED | cancel() |
| ORDERED | PARTIAL | receive() con items pendientes |
| ORDERED | RECEIVED | receive() con todos los items |
| ORDERED | CANCELLED | cancel() |
| PARTIAL | RECEIVED | receive() con items pendientes restantes |

Reglas de negocio:
- Solo se puede editar en estado DRAFT
- Solo se puede cancelar en DRAFT u ORDERED (no PARTIAL ni RECEIVED)
- Solo se puede recepcionar en ORDERED o PARTIAL
- `received_qty` nunca puede exceder `quantity`

## 10. Frontend

### Registro de plugin

```ts
// plugins/commerce/purchase/frontend/register.ts
export function register(ctx: PluginFrontendContext) {
  return {
    pluginId: "compras",
    routes: [
      {
        path: "commerce/purchase-orders",
        title: "Compras",
        component: PurchaseOrdersPage,
        requiredPermissions: ["compras.order.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/commerce/purchase-orders`,
        label: "Compras",
        requiredPermissions: ["compras.order.read"],
        group: "Gestión Comercial",
      },
    ],
  };
}
```

### Página principal (`PurchaseOrdersPage.tsx`)

DataTable con columnas:
- Proveedor (supplier.name)
- Estado (Badge: DRAFT=gris, ORDERED=azul, PARTIAL=amarillo, RECEIVED=verde, CANCELLED=rojo)
- Fecha (order_date)
- Items (N/M recibidos)
- Acciones (Editar, Confirmar, Recepcionar, Cancelar — según estado y permisos)

Barra de acciones:
- `[Nuevo proveedor]` — abre SupplierDialog (permiso: supplier.manage)
- `[Nueva orden]` — abre CreateOrderDialog (permiso: order.create)

### CreateOrderDialog

Diálogo con:
1. Combobox de proveedor (busca en suppliers activos)
2. Tabla de items con filas editables:
   - Combobox de producto (lista completa del catálogo)
   - Input cantidad
   - Input costo unitario
   - Botón eliminar fila
3. Botón "+ Agregar item"
4. Input expected_date, Textarea notes
5. Botón "Guardar borrador" (crea DRAFT) + Botón "Confirmar orden" (crea DRAFT y confirma)

### ReceiveOrderDialog

Diálogo con:
1. Select de warehouse (lista de lg_warehouses activos)
2. Lista de items pendientes (`received_qty < quantity`):
   - Checkbox para seleccionar
   - Input cantidad (default = pendiente restante)
   - Muestra: "X/Y recibidos"
3. Textarea notes
4. Botón "Recepcionar seleccionados"
5. Botón "Recepcionar todo pendiente" (marca todos con cantidad = pendiente)

### SupplierDialog

Diálogo con:
1. Input name (requerido)
2. Select document_type (catálogo de CRM)
3. Input document_number
4. Input email
5. Input phone
6. Input address
7. Textarea notes
8. Botón Guardar

## 11. Eventos

```
compras.order.created          → payload: { order_id, supplier_id, status }
compras.order.received         → payload: { order_id, warehouse_id, items_count, total_quantity }
compras.order.cancelled        → payload: { order_id, reason }
```

## 12. Criterios de aceptación

- [ ] Crear proveedor con datos mínimos (solo nombre)
- [ ] Crear orden DRAFT con 1+ items
- [ ] Confirmar orden → estado ORDERED
- [ ] Recepcionar todos los items → RECEIVED, stock incrementado vía API
- [ ] Recepcionar parcial → PARTIAL, stock incrementado por lo recibido
- [ ] Recepcionar duplicado de mismo item → 409 Conflict
- [ ] Cancelar orden ORDERED → CANCELLED
- [ ] Cancelar orden ya recepcionada → error 400
- [ ] Editar orden en DRAFT → ok, items se actualizan
- [ ] Editar orden en ORDERED → error 400
- [ ] Sidebar muestra "Gestión Comercial > Compras" solo con `compras.order.read`
- [ ] Driver (role driver) NO ve Compras en sidebar
- [ ] `idempotency_key` único por item+order garantiza no duplicar stock

## 13. Fuera de alcance (v2)

- Integración con facturación (relación con facturas de proveedor)
- Integración con cuentas por pagar
- Aprobaciones multi-nivel (workflow de autorización)
- Precios de compra históricos por producto/proveedor
- Conversión automática de unidades de medida
- Notificaciones por email al recepcionar
- Soporte para devoluciones a proveedor (`purchase_return`)
