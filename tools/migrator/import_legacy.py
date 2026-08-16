"""Migrador legacy (CSV tab-delimited) -> Systutor OSS PostgreSQL.

Ejecutar desde el venv del repo:
    .venv/bin/python tools/migrator/import_legacy.py [--dry-run]

Fases: catalogos -> productos(+precios/barcodes) -> grupos -> ADR ->
clientes(+direcciones/bancos) -> puntos de entrega -> cilindros(+retimbrado/PH/estado/servicios).

Idempotente por legacy_id: re-ejecutar no duplica.
"""
from __future__ import annotations

import csv
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

BUNDLE = Path.home() / "migracion_legacy" / "export_20260801"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from systutor.core.database import build_session_factory  # noqa: E402

from apps.api.app.config import get_settings  # noqa: E402
from plugins.crm.backend.models import (  # noqa: E402
    CrmCustomer,
    CrmCustomerAddress,
    CrmCustomerBankAccount,
    CrmPaymentTerm,
)
from plugins.logistics.backend.models.cylinder import (  # noqa: E402
    LogisticsCylinder,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
    LogisticsCylinderStateLog,
    LogisticsHydrostaticTest,
)
from plugins.logistics.backend.models.resources import (  # noqa: E402
    LogisticsDeliveryPoint,
    LogisticsWarehouse,
    LogisticsZone,
)
from plugins.productos.backend.models import (  # noqa: E402
    Product,
    ProductAdr,
    ProductBarcode,
    ProductBrand,
    ProductGroup,
    ProductInsumoType,
    ProductLine,
    ProductPrice,
    ProductStatus,
    ProductSubcategory,
    ProductSubline,
    ProductUnit,
)

DRY_RUN = "--dry-run" in sys.argv


def new_uuid() -> str:
    return str(uuid.uuid4())


def clean(value: str | None) -> str:
    if value is None:
        return ""
    return value.replace("\x00", "").strip()


def normalize_legacy_product_text(value: str) -> str:
    return value.replace("Industriall", "Industrial")


def num(value: str | None) -> float | None:
    v = clean(value)
    if not v or v == ".0000":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def idate(value: str | None) -> date | None:
    v = clean(value)
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def idt(value: str | None):
    v = clean(value)
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
    return None


def read_csv(name: str, fields: list[str]) -> list[dict[str, str]]:
    path = BUNDLE / f"{name}.csv"
    if not path.exists():
        print(f"  [skip] {name}.csv no existe")
        return []
    with path.open(encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, fieldnames=fields, delimiter="\t")
        return [dict(r) for r in reader if any(clean(v) for v in r.values())]


class Importer:
    def __init__(self, db: Session, tenant_id: str, branch_id: str, user_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.user_id = user_id
        self.created_by = user_id
        self.map_line: dict[str, str] = {}
        self.map_subline: dict[str, str] = {}
        self.map_brand: dict[str, str] = {}
        self.map_unit: dict[str, str] = {}
        self.map_insumo: dict[str, str] = {}
        self.map_subcat: dict[str, str] = {}
        self.map_group: dict[str, str] = {}
        self.map_status: dict[str, str] = {}
        self.map_zone: dict[str, str] = {}
        self.map_payment: dict[str, str] = {}
        self.map_product: dict[int, str] = {}
        self.map_customer: dict[int, str] = {}
        self.counters: dict[str, int] = {}

    def bump(self, key: str, n: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + n

    def _commit(self) -> None:
        if not DRY_RUN:
            self.db.commit()

    # ── Fase 1: catalogos ──────────────────────────────────────────
    def catalogs(self) -> None:
        print("== Fase 1: catalogos ==")

        # Líneas legacy: 1..49 (+ fila 17 derivada de grupos si falta)
        line_ids = set()
        for row in read_csv("linea", ["cod_Linea", "Desc_Linea"]):
            code, name = clean(row["cod_Linea"]), clean(row["Desc_Linea"])
            if not code or "<-" in name or "<-" in code:
                continue
            line_ids.add(code)
        for row in read_csv("grupo", ["Cod_Grupo", "ID_ProductoGas", "CodBar_ProductoGas", "Desc_Grupo", "id_Categoria", "Categoria", "id_Linea", "Desc_Linea", "id_SubLinea", "Desc_SubLinea", "id_unidad", "Desc_unidad", "Precio1", "Precio2", "Precio3", "Precio4"]):
            line_ids.add(clean(row["id_Linea"]))
        line_names = {}
        for row in read_csv("linea", ["cod_Linea", "Desc_Linea"]):
            if clean(row["cod_Linea"]):
                line_names[clean(row["cod_Linea"])] = clean(row["Desc_Linea"])
        for row in read_csv("grupo", ["Cod_Grupo", "ID_ProductoGas", "CodBar_ProductoGas", "Desc_Grupo", "id_Categoria", "Categoria", "id_Linea", "Desc_Linea", "id_SubLinea", "Desc_SubLinea", "id_unidad", "Desc_unidad", "Precio1", "Precio2", "Precio3", "Precio4"]):
            if clean(row["id_Linea"]) and clean(row["id_Linea"]) not in line_names:
                line_names[clean(row["id_Linea"])] = clean(row["Desc_Linea"])
        for code in sorted(line_ids):
            existing = self.db.scalar(select(ProductLine).where(ProductLine.tenant_id == self.tenant_id, ProductLine.code == code))
            if existing:
                self.map_line[code] = existing.id
                continue
            item = ProductLine(tenant_id=self.tenant_id, code=code, name=line_names.get(code, f"LINEA {code}"))
            self.db.add(item)
            self.db.flush()
            self.map_line[code] = item.id
            self.bump("lines")
        self._commit()

        for row in read_csv("sublinea", ["Cod_Sublinea", "Desc_SubLinea", "Cod_linea"]):
            code, name = clean(row["Cod_Sublinea"]), clean(row["Desc_SubLinea"])
            parent = self.map_line.get(clean(row["Cod_linea"]))
            if not code or not parent or "<-" in name:
                continue
            existing = self.db.scalar(select(ProductSubline).where(ProductSubline.tenant_id == self.tenant_id, ProductSubline.code == code))
            if existing:
                self.map_subline[code] = existing.id
                continue
            item = ProductSubline(tenant_id=self.tenant_id, code=code, name=name, line_id=parent)
            self.db.add(item)
            self.db.flush()
            self.map_subline[code] = item.id
            self.bump("sublines")
        self._commit()

        for row in read_csv("marca", ["Cod_Marca", "Desc_Marca"]):
            code, name = clean(row["Cod_Marca"]), clean(row["Desc_Marca"])
            if not code or "<-" in name:
                continue
            existing = self.db.scalar(select(ProductBrand).where(ProductBrand.tenant_id == self.tenant_id, ProductBrand.code == code))
            if existing:
                self.map_brand[code] = existing.id
                continue
            item = ProductBrand(tenant_id=self.tenant_id, code=code, name=name or f"MARCA {code}")
            self.db.add(item)
            self.db.flush()
            self.map_brand[code] = item.id
            self.bump("brands")
        self._commit()

        for row in read_csv("unidad", ["Cod_Unidad", "Desc_Unidad", "Equivalencia", "m3", "Litros", "Kilogramos"]):
            code, name = clean(row["Cod_Unidad"]), clean(row["Desc_Unidad"])
            if not code or "<-" in name:
                continue
            existing = self.db.scalar(select(ProductUnit).where(ProductUnit.tenant_id == self.tenant_id, ProductUnit.code == code))
            if existing:
                self.map_unit[code] = existing.id
                continue
            item = ProductUnit(
                tenant_id=self.tenant_id, code=code, name=name or f"UNIDAD {code}",
                equivalencia=int(num(row["Equivalencia"]) or 0) if num(row["Equivalencia"]) is not None else None,
                m3_factor=num(row["m3"]), liter_factor=num(row["Litros"]), kg_factor=num(row["Kilogramos"]),
            )
            self.db.add(item)
            self.db.flush()
            self.map_unit[code] = item.id
            self.bump("units")
        self._commit()

        for row in read_csv("tipoinsumo", ["Cod_TipoInsumo", "Desc_TipoInsumo"]):
            code, name = clean(row["Cod_TipoInsumo"]), clean(row["Desc_TipoInsumo"])
            if not code or "<-" in name:
                continue
            existing = self.db.scalar(select(ProductInsumoType).where(ProductInsumoType.tenant_id == self.tenant_id, ProductInsumoType.code == code))
            if existing:
                self.map_insumo[code] = existing.id
                continue
            item = ProductInsumoType(tenant_id=self.tenant_id, code=code, name=name or f"INSUMO {code}")
            self.db.add(item)
            self.db.flush()
            self.map_insumo[code] = item.id
            self.bump("insumo_types")
        self._commit()

        for row in read_csv("subcategoria", ["codigo", "Descripcion"]):
            code, name = clean(row["codigo"]), clean(row["Descripcion"])
            if not code or "<-" in name:
                continue
            existing = self.db.scalar(select(ProductSubcategory).where(ProductSubcategory.tenant_id == self.tenant_id, ProductSubcategory.code == code))
            if existing:
                self.map_subcat[code] = existing.id
                continue
            item = ProductSubcategory(tenant_id=self.tenant_id, code=code, name=name or f"SUBCAT {code}")
            self.db.add(item)
            self.db.flush()
            self.map_subcat[code] = item.id
            self.bump("subcategories")
        self._commit()

        for row in read_csv("estadoproducto", ["cod_estado", "Desc_estado"]):
            code = clean(row["cod_estado"])
            legacy_status = self.db.scalar(select(ProductStatus).where(ProductStatus.code == code))
            if legacy_status:
                self.map_status[code] = legacy_status.code
        # mapeo por defecto: 1->ACTIVO, 2->INACTIVO
        self.map_status.setdefault("1", "ACTIVO")
        self.map_status.setdefault("2", "INACTIVO")

        for row in read_csv("zona", ["Cod_Zona", "Zona", "Cod_Distrito"]):
            code, name = clean(row["Cod_Zona"]), clean(row["Zona"])
            if not code or "<-" in name:
                continue
            existing = self.db.scalar(select(LogisticsZone).where(LogisticsZone.tenant_id == self.tenant_id, LogisticsZone.code == code))
            if existing:
                self.map_zone[code] = existing.id
                continue
            item = LogisticsZone(tenant_id=self.tenant_id, code=code, name=name or f"ZONA {code}")
            self.db.add(item)
            self.db.flush()
            self.map_zone[code] = item.id
            self.bump("zones")
        self._commit()

        # Formas de pago: mapeo semantico, fallback FORMA_<id>
        payment_map = {
            "1": "CONTADO", "4": "CONTADO", "3": "TARJETA", "7": "TARJETA",
            "5": "TRANSFERENCIA", "8": "TRANSFERENCIA",
            "2": "REMESA_30", "6": "REMESA_30", "17": "REMESA_30", "19": "REMESA_60",
            "15": "CREDITO_30", "16": "CREDITO_60", "18": "CREDITO_30", "9": "CHEQUE",
        }
        for row in read_csv("formas_pago", ["Id_FormaPago", "Descripcion", "TipoOperacion", "RequiereAutorizacion", "PlazoPago", "Activo"]):
            code = clean(row["Id_FormaPago"])
            if not code:
                continue
            target = payment_map.get(code)
            if target:
                existing = self.db.scalar(select(CrmPaymentTerm).where(CrmPaymentTerm.code == target))
                if existing:
                    self.map_payment[code] = existing.code
                    continue
            existing = self.db.scalar(select(CrmPaymentTerm).where(CrmPaymentTerm.code == f"FORMA_{code}"))
            if existing:
                self.map_payment[code] = existing.code
                continue
            item = CrmPaymentTerm(code=f"FORMA_{code}", name=clean(row["Descripcion"]) or f"Forma {code}")
            self.db.add(item)
            self.db.flush()
            self.map_payment[code] = item.code
            self.bump("payment_terms")
        self._commit()
        print(f"  catalogos OK: lines={self.counters.get('lines',0)} sublines={self.counters.get('sublines',0)} units={self.counters.get('units',0)} zonas={self.counters.get('zones',0)}")

    # ── Fase 1b: almacenes legacy -> lg_warehouses ──────────────
    def warehouses(self) -> None:
        print("== Fase 1b: almacenes ==")
        fields = ["Cod_Almacen", "Desc_Almacen", "Direccion_Almacen", "Ruc_Almacen", "Telf_Almacen", "Cod_RazonSocial", "Mostrar", "Formato_precios", "Activo"]
        for row in read_csv("almacen", fields):
            code = clean(row["Cod_Almacen"])
            if not code:
                continue
            existing = self.db.scalar(select(LogisticsWarehouse).where(LogisticsWarehouse.tenant_id == self.tenant_id, LogisticsWarehouse.code == code))
            if existing:
                continue
            address = clean(row["Direccion_Almacen"])
            if len(address) > 200:
                address = address[:200]
            name = clean(row["Desc_Almacen"])
            if len(name) > 100:
                name = name[:100]
            self.db.add(LogisticsWarehouse(
                tenant_id=self.tenant_id,
                branch_id=self.branch_id,
                name=name or f"ALMACEN {code}",
                code=code,
                address=address or None,
                phone=clean(row["Telf_Almacen"]) or None,
                warehouse_type="FIXED",
                is_active=clean(row["Activo"]) != "0",
            ))
            self.bump("warehouses")
        self._commit()
        print(f"  almacenes OK: {self.counters.get('warehouses',0)}")

    # ── Fase 2: productos ───────────────────────────────────────────
    def products(self) -> None:
        print("== Fase 2: productos ==")
        fields = ["cod_producto", "Nro_Producto", "Desc_Producto", "StockMin_Producto", "Cod_Linea", "Cod_TipoInsumo", "Cod_Unidad", "Cod_UnidadCja", "Precio_Producto", "PrecioCja_Producto", "Costo_Producto", "peso_producto", "Marca_Producto", "Estado_Producto", "cIGV", "cant", "Cont", "cod_SubCategoria", "cod_grupo", "costo_total", "eliminar", "servicio", "barcode1", "barcode2", "stock", "lista2", "lista3", "lista4", "condicion", "M3", "ADR_Categoria", "ADR_TipoBulto", "ADR_PesoKg", "ADR_M3", "ADR_UN", "ADR_Mercancia", "ADR_Etiqueta", "ADR_Tunel", "ADR_Sublinea", "ADR_Factor", "ADR_Puntos", "ADR_UnidadMedida", "PaisCodigo"]
        default_unit = next(iter(self.map_unit.values())) if self.map_unit else None
        default_line = next(iter(self.map_line.values())) if self.map_line else None
        used_barcodes: set[tuple[str, str]] = set()
        for row in read_csv("producto", fields):
            legacy_id = int(float(clean(row["cod_producto"]))) if clean(row["cod_producto"]) else 0
            existing = self.db.scalar(select(Product).where(Product.tenant_id == self.tenant_id, Product.legacy_id == legacy_id))
            if existing:
                self.map_product[legacy_id] = existing.id
                continue
            sku = normalize_legacy_product_text(clean(row["Nro_Producto"]) or str(legacy_id))
            if len(sku) > 30:
                sku = sku[:30]
            name = normalize_legacy_product_text(
                clean(row["Desc_Producto"]) or f"PRODUCTO {legacy_id}"
            )
            if len(name) > 200:
                name = name[:200]
            line_ref = clean(row["Cod_Linea"])
            subline_id = self.map_subline.get(line_ref)
            line_id = self.map_line.get(line_ref) or default_line
            if line_id is None:
                self.bump("products_rejected")
                print(f"  [reject] producto {legacy_id}: sin linea")
                continue
            condition_code = clean(row["condicion"]) or "PRODUCTO"
            if condition_code == "zzSERVICIO":
                condition_code = "SERVICIO"
            existing = self.db.scalar(select(Product).where(Product.tenant_id == self.tenant_id, Product.sku == sku))
            if existing:
                self.map_product[legacy_id] = existing.id
                self.bump("products_sku_dedup")
                continue
            status_code = self.map_status.get(clean(row["Estado_Producto"]), "ACTIVO")
            is_active = clean(row["eliminar"]) != "1" and status_code != "INACTIVO"
            currency = "EUR" if clean(row["PaisCodigo"]) == "ES" else "PEN"
            item = Product(
                tenant_id=self.tenant_id,
                legacy_id=legacy_id,
                sku=sku,
                name=name,
                description=name,
                line_id=line_id,
                subline_id=subline_id,
                brand_id=self.map_brand.get(clean(row["Marca_Producto"])),
                insumo_type_id=self.map_insumo.get(clean(row["Cod_TipoInsumo"])),
                unit_id=self.map_unit.get(clean(row["Cod_Unidad"])) or default_unit,
                box_unit_id=self.map_unit.get(clean(row["Cod_UnidadCja"])),
                status_code=status_code,
                condition_code=condition_code,
                weight_kg=num(row["peso_producto"]),
                default_weight_kg=num(row["peso_producto"]),
                content_m3=num(row["M3"]),
                country_code=clean(row["PaisCodigo"]) or "PER",
                is_service=clean(row["servicio"]) == "1",
                is_active=is_active,
                created_by=self.created_by,
            )
            self.db.add(item)
            self.db.flush()
            self.map_product[legacy_id] = item.id
            self.bump("products")

            base_price = num(row["Precio_Producto"])
            price_lists = [("LISTA1", base_price), ("LISTA2", num(row["lista2"])), ("LISTA3", num(row["lista3"])), ("LISTA4", num(row["lista4"]))]
            for pl, amount in price_lists:
                if amount is None or amount <= 0:
                    continue
                self.db.add(ProductPrice(
                    tenant_id=self.tenant_id, product_id=item.id, price_list=pl, amount=amount,
                    currency=currency, valid_from=date(2026, 1, 1), created_by=self.created_by,
                ))
                self.bump("prices")

            for barcode, btype, primary in ((clean(row["barcode1"]), "BARCODE1", True), (clean(row["barcode2"]), "BARCODE2", False)):
                if not barcode:
                    continue
                if (btype, barcode) in used_barcodes:
                    self.bump("barcodes_dup")
                    continue
                used_barcodes.add((btype, barcode))
                self.db.add(ProductBarcode(
                    tenant_id=self.tenant_id, product_id=item.id, barcode_type=btype,
                    barcode=barcode[:150], is_primary=primary,
                ))
                self.bump("barcodes")
        self._commit()
        print(f"  productos OK: {self.counters.get('products',0)} (dedup sku={self.counters.get('products_sku_dedup',0)}, rechazados={self.counters.get('products_rejected',0)}) precios={self.counters.get('prices',0)} barcodes={self.counters.get('barcodes',0)}")

    # ── Fase 3: grupos (gas_product_id post-productos) ─────────────
    def groups(self) -> None:
        print("== Fase 3: grupos ==")
        fields = ["Cod_Grupo", "ID_ProductoGas", "CodBar_ProductoGas", "Desc_Grupo", "id_Categoria", "Categoria", "id_Linea", "Desc_Linea", "id_SubLinea", "Desc_SubLinea", "id_unidad", "Desc_unidad", "Precio1", "Precio2", "Precio3", "Precio4"]
        for row in read_csv("grupo", fields):
            code = clean(row["Cod_Grupo"])
            if not code or "<-" in clean(row["Desc_Grupo"]):
                continue
            gas_product_id = None
            try:
                gas_product_id = self.map_product.get(int(float(clean(row["ID_ProductoGas"]))))
            except (ValueError, KeyError):
                pass
            existing = self.db.scalar(select(ProductGroup).where(ProductGroup.tenant_id == self.tenant_id, ProductGroup.code == code))
            if existing:
                if gas_product_id:
                    existing.gas_product_id = gas_product_id
                    self.db.add(existing)
                self.map_group[code] = existing.id
                continue
            item = ProductGroup(
                tenant_id=self.tenant_id, code=code, name=clean(row["Desc_Grupo"])[:50] or f"GRUPO {code}",
                gas_product_id=gas_product_id,
                line_id=self.map_line.get(clean(row["id_Linea"])),
                subline_id=self.map_subline.get(clean(row["id_SubLinea"])),
                unit_id=self.map_unit.get(clean(row["id_unidad"])),
            )
            self.db.add(item)
            self.db.flush()
            self.map_group[code] = item.id
            self.bump("groups")
        self._commit()
        print(f"  grupos OK: {self.counters.get('groups',0)}")

    # ── Fase 4: ADR ────────────────────────────────────────────────
    def adr(self) -> None:
        print("== Fase 4: ADR ==")
        product_fields = ["cod_producto", "Nro_Producto", "Desc_Producto", "StockMin_Producto", "Cod_Linea", "Cod_TipoInsumo", "Cod_Unidad", "Cod_UnidadCja", "Precio_Producto", "PrecioCja_Producto", "Costo_Producto", "peso_producto", "Marca_Producto", "Estado_Producto", "cIGV", "cant", "Cont", "cod_SubCategoria", "cod_grupo", "costo_total", "eliminar", "servicio", "barcode1", "barcode2", "stock", "lista2", "lista3", "lista4", "condicion", "M3", "ADR_Categoria", "ADR_TipoBulto", "ADR_PesoKg", "ADR_M3", "ADR_UN", "ADR_Mercancia", "ADR_Etiqueta", "ADR_Tunel", "ADR_Sublinea", "ADR_Factor", "ADR_Puntos", "ADR_UnidadMedida", "PaisCodigo"]
        gas_by_group: dict[str, str] = {}
        for row in read_csv("producto", product_fields):
            try:
                legacy_id = int(float(clean(row["cod_producto"])))
            except ValueError:
                continue
            product_id = self.map_product.get(legacy_id)
            if not product_id:
                continue
            if clean(row["condicion"]) == "GAS":
                gas_by_group[clean(row["cod_grupo"])] = product_id
            else:
                gas_by_group.setdefault(clean(row["cod_grupo"]), product_id)
        # 4.1 ADR desde los campos ADR_* del propio producto (gas/mercancia)
        for row in read_csv("producto", product_fields):
            try:
                legacy_id = int(float(clean(row["cod_producto"])))
            except ValueError:
                continue
            product_id = self.map_product.get(legacy_id)
            un_number = clean(row["ADR_UN"])
            if not product_id or not (un_number or clean(row["ADR_Mercancia"])):
                continue
            existing = self.db.scalar(select(ProductAdr).where(ProductAdr.product_id == product_id, ProductAdr.valid_from == date(2026, 1, 1), ProductAdr.valid_to.is_(None)))
            if existing:
                continue
            self.db.add(ProductAdr(
                tenant_id=self.tenant_id, product_id=product_id,
                category=clean(row["ADR_Categoria"]) or None,
                packaging_type=clean(row["ADR_TipoBulto"]) or None,
                net_weight_kg=num(row["ADR_PesoKg"]),
                net_volume_m3=num(row["ADR_M3"]),
                un_number=un_number or None,
                cargo_description=clean(row["ADR_Mercancia"]) or None,
                label=clean(row["ADR_Etiqueta"]) or None,
                tunnel_restriction=clean(row["ADR_Tunel"]) or None,
                subline_id=self.map_subline.get(clean(row["ADR_Sublinea"])),
                factor=int(num(row["ADR_Factor"])) if num(row["ADR_Factor"]) is not None else None,
                points=int(num(row["ADR_Puntos"])) if num(row["ADR_Puntos"]) is not None else None,
                unit_measure=clean(row["ADR_UnidadMedida"]) or None,
                valid_from=date(2026, 1, 1), valid_to=None,
                created_by=self.created_by,
            ))
            self.bump("adr")
        # 4.2 Edetalle_Producto_Bombona (ADR del envase por grupo)
        fields = ["Id_PROD_Bombonas", "CATEG_transp", "TIPO_DE_BULTO", "CANTIDAD_NETA", "UNIDAD", "M3_gas", "PESO_NETO_KG", "DENOMINACION_MERCANCIA", "NRO_ONU", "PRODUCTO_TRANSPORTADO", "ETIQUETA", "TUNEL", "SUBLINEA_PROD", "VigenteDesde", "VigenteHasta"]
        for row in read_csv("edetalle_bombona", fields):
            group_code = clean(row["Id_PROD_Bombonas"])
            product_id = gas_by_group.get(group_code)
            if product_id is None:
                self.bump("adr_rejected")
                print(f"  [reject] adr grupo {group_code}: sin producto")
                continue
            existing = self.db.scalar(select(ProductAdr).where(ProductAdr.product_id == product_id, ProductAdr.un_number == clean(row["NRO_ONU"]), ProductAdr.valid_from == (idate(row["VigenteDesde"]) or date(2026, 1, 1))))
            if existing:
                self.bump("adr_dups")
                continue
            self.db.add(ProductAdr(
                tenant_id=self.tenant_id,
                product_id=product_id,
                category=clean(row["CATEG_transp"]) or None,
                packaging_type=clean(row["TIPO_DE_BULTO"]) or None,
                net_weight_kg=num(row["PESO_NETO_KG"]),
                net_volume_m3=num(row["M3_gas"]),
                un_number=clean(row["NRO_ONU"]) or None,
                cargo_description=clean(row["DENOMINACION_MERCANCIA"]) or clean(row["PRODUCTO_TRANSPORTADO"]) or None,
                label=clean(row["ETIQUETA"]) or None,
                tunnel_restriction=clean(row["TUNEL"]) or None,
                subline_id=self.map_subline.get(clean(row["SUBLINEA_PROD"])),
                valid_from=idate(row["VigenteDesde"]) or date(2026, 1, 1),
                valid_to=idate(row["VigenteHasta"]),
                created_by=self.created_by,
            ))
            self.bump("adr")
        self._commit()
        print(f"  ADR OK: {self.counters.get('adr',0)} (rechazados={self.counters.get('adr_rejected',0)}, dups={self.counters.get('adr_dups',0)})")

    # ── Fase 5: clientes ───────────────────────────────────────────
    def customers(self) -> None:
        print("== Fase 5: clientes ==")
        fields = ["Cod_Persona", "Nro_Persona", "Nom_Persona", "Dni_Persona", "Ruc_Persona", "Cod_TipoPersona", "Sexo_Persona", "FNac_Personal", "mail_Persona", "Telefono_Persona", "Activo", "Login_Persona", "Pass_Persona", "Nick_Persona", "Fotografia", "id_clave_Operacion", "clave_op_intracomunitaria", "nombre_comercial", "observaciones", "Documento_Principal", "Tipo_facturacion", "Id_FormaPago", "Id_Direccion_Fiscal", "PaisCodigo", "TipoIdentificacionFiscal", "NumeroIdentificacionFiscal", "CodigoActividadPrincipal", "DescripcionActividadPrincipal", "ActividadValidada", "FechaValidacionActividad", "FuenteValidacionActividad"]
        doc_types = {"RUC": "RUC", "DNI": "DNI", "NIF": "NIF", "NIE": "NIE", "PASAPORTE": "PASAPORTE", "PASSPORT": "PASAPORTE", "NIT": "OTRO", "CIF": "NIF", "V": "OTRO", "E": "OTRO", "J": "OTRO", "CEDULA": "OTRO", "RIF": "OTRO"}
        used_docs: set[tuple[str, str]] = set()
        addr_by_id: dict[str, dict[str, str]] = {}
        for row in read_csv("direccion", ["Id_Direccion", "Linea1", "Linea2", "Codigo_Postal", "Id_Zona", "Ubigeo", "Latitud", "Longitud", "Observaciones", "Activo", "Fecha_Alta", "Id_Localidad", "Formatted_Address", "Place_Id", "Country_Code", "Admin_Area_1", "Admin_Area_2", "Localidad", "Street_Name", "Street_Number", "Fuente_Geocod", "Precision_Metros", "Capturado_Por", "Capturado_En"]):
            addr_by_id[clean(row["Id_Direccion"])] = row
        for row in read_csv("persona", fields):
            legacy_id = int(float(clean(row["Cod_Persona"]))) if clean(row["Cod_Persona"]) else 0
            existing = self.db.scalar(select(CrmCustomer).where(CrmCustomer.external_code == str(legacy_id)))
            if existing:
                self.map_customer[legacy_id] = existing.id
                continue
            doc_type = doc_types.get(clean(row["TipoIdentificacionFiscal"]).upper())
            doc_number = clean(row["NumeroIdentificacionFiscal"]) or clean(row["Ruc_Persona"]) or clean(row["Dni_Persona"])
            if doc_type is None:
                if doc_number and len(doc_number) >= 11:
                    doc_type, doc_number = "RUC", doc_number
                elif doc_number:
                    doc_type, doc_number = "DNI", doc_number
                else:
                    doc_type = "OTRO"
            if not doc_number:
                doc_number = f"SIN-DOC-{legacy_id}"
            doc_key = (doc_type, doc_number)
            if doc_key in used_docs:
                doc_number = f"{doc_number[:26]}-{legacy_id}"
                doc_key = (doc_type, doc_number)
                self.bump("customers_doc_dedup")
            used_docs.add(doc_key)
            legal_name = clean(row["Nom_Persona"]) or f"CLIENTE {legacy_id}"
            if len(legal_name) > 200:
                legal_name = legal_name[:200]
            item = CrmCustomer(
                tenant_id=self.tenant_id,
                external_code=str(legacy_id),
                legal_name=legal_name,
                commercial_name=clean(row["nombre_comercial"]) or None,
                document_type_code=doc_type,
                document_number=doc_number[:30],
                country_code=clean(row["PaisCodigo"]) or "PER",
                email=clean(row["mail_Persona"]) or None,
                phone=clean(row["Telefono_Persona"]) or None,
                economic_activity_code=clean(row["CodigoActividadPrincipal"]) or None,
                economic_activity_description=clean(row["DescripcionActividadPrincipal"]) or None,
                activity_validated=clean(row["ActividadValidada"]) == "1",
                activity_validation_source=clean(row["FuenteValidacionActividad"]) or None,
                activity_validation_date=idt(row["FechaValidacionActividad"]),
                payment_term_code=self.map_payment.get(clean(row["Id_FormaPago"])),
                billing_type=clean(row["Tipo_facturacion"]) or None,
                gender={"Masculino": "M", "Femenino": "F"}.get(clean(row["Sexo_Persona"])),
                birth_date=idate(row["FNac_Personal"]),
                notes=clean(row["observaciones"]) or None,
                is_active=clean(row["Activo"]) != "0",
                created_by=self.created_by,
            )
            self.db.add(item)
            self.db.flush()
            self.map_customer[legacy_id] = item.id
            self.bump("customers")

            fiscal_ref = clean(row["Id_Direccion_Fiscal"])
            addr = addr_by_id.get(fiscal_ref)
            if addr and clean(addr["Linea1"]):
                line1 = clean(addr["Linea1"])
                if len(line1) > 200:
                    line1 = line1[:200]
                address = CrmCustomerAddress(
                    tenant_id=self.tenant_id, customer_id=item.id, address_type="FISCAL",
                    line1=line1, line2=clean(addr["Linea2"]) or None,
                    city=clean(addr["Localidad"]) or None,
                    state=clean(addr["Admin_Area_1"]) or None,
                    district=clean(addr["Admin_Area_2"]) or clean(addr["Localidad"]) or None,
                    postal_code=clean(addr["Codigo_Postal"]) or None,
                    country_code=clean(addr["Country_Code"]) or clean(row["PaisCodigo"]) or "PER",
                    latitude=num(addr["Latitud"]), longitude=num(addr["Longitud"]),
                    place_id=clean(addr["Place_Id"]) or None,
                    formatted_address=clean(addr["Formatted_Address"]) or None,
                    street_name=clean(addr["Street_Name"]) or None,
                    street_number=clean(addr["Street_Number"]) or None,
                    geocode_source=clean(addr["Fuente_Geocod"]) or None,
                    precision_meters=int(num(addr["Precision_Metros"])) if num(addr["Precision_Metros"]) is not None else None,
                )
                self.db.add(address)
                self.db.flush()
                item.fiscal_address_id = address.id
                self.db.add(item)
                self.bump("addresses")
        self._commit()

        # Cuentas bancarias
        for row in read_csv("datos_bancarios", ["Id_DatoBancario", "Cod_Responsable", "Id_ClientePersona", "Numero_Cuenta", "Forma_Pago", "Activo", "Fecha_Alta", "Fecha_Baja", "Motivo_Baja", "Usuario_Baja", "IdBanco"]):
            customer_id = None
            try:
                customer_id = self.map_customer.get(int(float(clean(row["Id_ClientePersona"]))))
            except (ValueError, KeyError):
                pass
            if not customer_id:
                self.bump("bank_rejected")
                continue
            account_number = clean(row["Numero_Cuenta"])
            if not account_number:
                continue
            existing = self.db.scalar(select(CrmCustomerBankAccount).where(CrmCustomerBankAccount.customer_id == customer_id, CrmCustomerBankAccount.iban == account_number[:34]))
            if existing:
                continue
            self.db.add(CrmCustomerBankAccount(
                tenant_id=self.tenant_id, customer_id=customer_id,
                bank_name="LEGACY", account_holder=self.db.get(CrmCustomer, customer_id).legal_name,
                iban=account_number[:34], is_active=clean(row["Activo"]) != "0",
            ))
            self.bump("bank_accounts")
        self._commit()
        print(f"  clientes OK: {self.counters.get('customers',0)} direcciones={self.counters.get('addresses',0)} bancos={self.counters.get('bank_accounts',0)} (rechazados={self.counters.get('bank_rejected',0)})")

    # ── Fase 6: puntos de entrega ──────────────────────────────────
    def delivery_points(self) -> None:
        print("== Fase 6: puntos de entrega ==")
        fields = ["Codigo", "Id_ClientePersona", "Direccion", "Contacto", "Telefono", "Correoresp", "Enlace_GPS", "Id_Zona", "Dreparto", "Id_Agente_Asignado", "Id_DatoBancario", "Observ_Responsable", "Principal", "Activo", "Fecha_Registro", "ubigeo", "Dvisita", "garantia", "Envio", "Id_Sucursal", "Id_Direccion", "NombrePunto", "VentanaHorario", "Indicaciones", "Id_RutaAsignada", "UsuarioCrea", "FechaCrea", "UsuarioMod", "FechaMod", "RowVersion", "TiempoServicioMin", "DemandaUnidades", "DemandaPesoKg", "PaisCodigo", "Documento_Fiscal_Operacion", "TipoOperacionFiscal"]
        customer_names: dict[int, str] = {}
        for row in read_csv("persona", ["Cod_Persona", "Nro_Persona", "Nom_Persona", "Dni_Persona", "Ruc_Persona", "Cod_TipoPersona", "Sexo_Persona", "FNac_Personal", "mail_Persona", "Telefono_Persona", "Activo", "Login_Persona", "Pass_Persona", "Nick_Persona", "Fotografia", "id_clave_Operacion", "clave_op_intracomunitaria", "nombre_comercial", "observaciones", "Documento_Principal", "Tipo_facturacion", "Id_FormaPago", "Id_Direccion_Fiscal", "PaisCodigo", "TipoIdentificacionFiscal", "NumeroIdentificacionFiscal", "CodigoActividadPrincipal", "DescripcionActividadPrincipal", "ActividadValidada", "FechaValidacionActividad", "FuenteValidacionActividad"]):
            try:
                customer_names[int(float(clean(row["Cod_Persona"])))] = clean(row["Nom_Persona"])
            except ValueError:
                continue
        for row in read_csv("vehiculo_cliente", fields):
            legacy_id = clean(row["Codigo"])
            customer_id = None
            try:
                customer_id = self.map_customer.get(int(float(clean(row["Id_ClientePersona"]))))
            except (ValueError, KeyError):
                pass
            if not customer_id:
                self.bump("dp_rejected")
                print(f"  [reject] punto entrega {legacy_id}: cliente {row['Id_ClientePersona']} no mapeado")
                continue
            existing = self.db.scalar(select(LogisticsDeliveryPoint).where(LogisticsDeliveryPoint.customer_id == customer_id, LogisticsDeliveryPoint.address == clean(row["Direccion"])))
            if existing:
                self.bump("dp_dups")
                continue
            address = clean(row["Direccion"]) or "SIN DIRECCION"
            if len(address) > 200:
                address = address[:200]
            self.db.add(LogisticsDeliveryPoint(
                tenant_id=self.tenant_id,
                customer_id=customer_id,
                customer_name=(customer_names.get(int(float(clean(row["Id_ClientePersona"])))) or "CLIENTE")[:120],
                contact_name=clean(row["Contacto"]) or None,
                contact_email=clean(row["Correoresp"]) or None,
                address=address,
                phone=clean(row["Telefono"]) or None,
                zone_id=self.map_zone.get(clean(row["Id_Zona"])),
                is_primary=clean(row["Principal"]) == "1",
                delivery_day=clean(row["Dvisita"]) or None,
                visit_day=clean(row["Dreparto"]) or None,
                time_window=clean(row["VentanaHorario"]) or None,
                instructions=clean(row["Indicaciones"]) or None,
                service_time_min=int(num(row["TiempoServicioMin"])) if num(row["TiempoServicioMin"]) is not None else None,
                demand_units=int(num(row["DemandaUnidades"])) if num(row["DemandaUnidades"]) is not None else None,
                demand_weight_kg=num(row["DemandaPesoKg"]),
                gps_link=clean(row["Enlace_GPS"]) or None,
                fiscal_operation_document=clean(row["Documento_Fiscal_Operacion"]) or None,
                fiscal_operation_type=clean(row["TipoOperacionFiscal"]) or None,
                is_active=clean(row["Activo"]) != "0",
            ))
            self.bump("delivery_points")
        self._commit()
        print(f"  puntos de entrega OK: {self.counters.get('delivery_points',0)} (rechazados={self.counters.get('dp_rejected',0)}, dups={self.counters.get('dp_dups',0)})")


    # ── Fase 9: stock calculado legacy (fórmula SUM StkIngreso-StkEgreso) ──
    def stock(self) -> None:
        print("== Fase 9: stock calculado ==")
        from sqlalchemy import text

        csv_path = BUNDLE.parent / "stock_calculado.csv"
        if not csv_path.exists():
            print("  [skip] stock_calculado.csv no existe")
            return
        with csv_path.open(encoding="utf-8", errors="replace") as fh:
            rows = list(csv.DictReader(fh, fieldnames=["cod_producto", "stock_calc"], delimiter="\t"))
        warehouse_id = self.db.execute(text(
            "SELECT id FROM lg_warehouses WHERE is_primary = TRUE LIMIT 1"
        )).scalar_one()
        applied = 0
        for row in rows:
            try:
                legacy_id = int(float(clean(row.get("cod_producto", ""))))
                stock = float(row.get("stock_calc", "") or 0)
            except ValueError:
                continue
            if stock <= 0:
                continue
            product_id = self.map_product.get(legacy_id)
            if not product_id:
                continue
            updated = self.db.execute(text(
                "UPDATE stk_balance SET quantity = :q, updated_at = now() "
                "WHERE product_id = :pid AND warehouse_id = :w AND quantity = 0"
            ), {"q": stock, "pid": product_id, "w": str(warehouse_id)})
            if updated.rowcount:  # type: ignore[union-attr]
                applied += 1
        self._commit()
        print(f"  stock calculado aplicado: {applied}")

    # ── Fase 7: cilindros + retimbrado + PH + estado + servicios ───
    def cylinders(self) -> None:
        print("== Fase 7: cilindros ==")
        product_fields = ["cod_producto", "Nro_Producto", "Desc_Producto", "StockMin_Producto", "Cod_Linea", "Cod_TipoInsumo", "Cod_Unidad", "Cod_UnidadCja", "Precio_Producto", "PrecioCja_Producto", "Costo_Producto", "peso_producto", "Marca_Producto", "Estado_Producto", "cIGV", "cant", "Cont", "cod_SubCategoria", "cod_grupo", "costo_total", "eliminar", "servicio", "barcode1", "barcode2", "stock", "lista2", "lista3", "lista4", "condicion", "M3", "ADR_Categoria", "ADR_TipoBulto", "ADR_PesoKg", "ADR_M3", "ADR_UN", "ADR_Mercancia", "ADR_Etiqueta", "ADR_Tunel", "ADR_Sublinea", "ADR_Factor", "ADR_Puntos", "ADR_UnidadMedida", "PaisCodigo"]
        gas_by_group: dict[str, str] = {}
        envase_rows: list[dict[str, str]] = []
        for row in read_csv("producto", product_fields):
            condition = clean(row["condicion"])
            try:
                legacy_id = int(float(clean(row["cod_producto"])))
            except ValueError:
                continue
            product_id = self.map_product.get(legacy_id)
            if condition == "GAS":
                if product_id:
                    gas_by_group[clean(row["cod_grupo"])] = product_id
            elif condition in ("CILPRO", "CILCLI", "CILGAR", "CILPROV"):
                envase_rows.append(row)
        serial_used: set[str] = set()
        barcode_used: set[str] = set()
        service_type = self.db.execute(text("SELECT id FROM lg_service_types ORDER BY name LIMIT 1")).scalar()
        for row in envase_rows:
            legacy_id = int(float(clean(row["cod_producto"]))) if clean(row["cod_producto"]) else 0
            serial = clean(row["barcode2"]) or clean(row["barcode1"]) or clean(row["Nro_Producto"]) or str(legacy_id)
            existing = self.db.scalar(select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == self.tenant_id, LogisticsCylinder.serial == serial))
            if existing:
                self.bump("cylinders_existing")
                continue
            if serial in serial_used:
                self.bump("cylinders_serial_dup")
                serial = f"{serial}-{legacy_id}"
            serial_used.add(serial)
            barcode1 = clean(row["barcode1"]) or None
            barcode2 = clean(row["barcode2"]) or clean(row["Nro_Producto"]) or None
            if serial and not barcode2:
                barcode2 = serial
            if barcode1 and barcode1 in barcode_used:
                barcode1 = None
            if barcode1:
                barcode_used.add(barcode1)
            if barcode2 and barcode2 in barcode_used:
                barcode2 = None
            if barcode2:
                barcode_used.add(barcode2)
            gas_product_id = gas_by_group.get(clean(row["cod_grupo"]))
            item = LogisticsCylinder(
                tenant_id=self.tenant_id,
                branch_id=self.branch_id,
                serial=serial[:50],
                description=clean(row["Desc_Producto"])[:200] or None,
                barcode1=barcode1,
                barcode2=barcode2,
                current_state="EN_ALMACEN_VACIO",
                gas_group_id=gas_product_id,
                product_id=gas_product_id,
                condition=clean(row["condicion"]),
                brand_id=self.map_brand.get(clean(row["Marca_Producto"])),
                weight_origin=num(row["peso_producto"]),
                weight_current=num(row["peso_producto"]),
                manufacturer_date=None,
                is_active=clean(row["eliminar"]) != "1",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(item)
            self.db.flush()
            self.bump("cylinders")

            # retimbrados del envase (por Cod_producto)
            for r in read_csv("retimbrado", ["Id", "Cod_producto", "Codigo_fabricacion", "Anio_fabricacion", "Nro_Bombona", "Peso_origen", "Peso_actual", "Presion_servicio", "Presion_prueba", "Nro_aprobacion", "Clase_peligro", "Marcado1", "Marcado2", "Formato_Bulto", "Transporte", "Etiqueta", "Tuneles", "Nro_ONU", "Regist_Alimentario"]):
                if clean(r["Cod_producto"]) != str(legacy_id):
                    continue
                ret_date = idate(r.get("Fecha_retimbrado", ""))
                self.db.add(LogisticsCylinderRetimbrado(
                    cylinder_id=item.id,
                    retimbrado_date=ret_date or item.created_at.date(),
                    manufacture_code=clean(r["Codigo_fabricacion"]) or None,
                    manufacture_year=int(num(r["Anio_fabricacion"])) if num(r["Anio_fabricacion"]) is not None else None,
                    serial_number=clean(r["Nro_Bombona"]) or None,
                    weight_origin=num(r["Peso_origen"]),
                    weight_current=num(r["Peso_actual"]),
                    service_pressure=num(r["Presion_servicio"]),
                    test_pressure=num(r["Presion_prueba"]),
                    approval_number=clean(r["Nro_aprobacion"]) or None,
                    danger_class=clean(r["Clase_peligro"]) or None,
                    marking1=clean(r["Marcado1"]) or None,
                    marking2=clean(r["Marcado2"]) or None,
                    package_format=clean(r["Formato_Bulto"]) or None,
                    transport_code=int(num(r["Transporte"])) if num(r["Transporte"]) is not None else None,
                    adr_label=clean(r["Etiqueta"]) or None,
                    adr_tunnel=clean(r["Tuneles"]) or None,
                    un_number=clean(r["Nro_ONU"]) or None,
                    food_registry=clean(r["Regist_Alimentario"]) or None,
                    created_by=self.created_by,
                ))
                self.bump("retimbrados")
            # PH (Eph.Id_Cilindro = cod producto del envase)
            for ph in read_csv("eph", ["Id_Cilindro", "Fecha_PH", "Estado", "Modificado_por", "Fecha_PH_Anterior"]):
                if clean(ph["Id_Cilindro"]) != str(legacy_id):
                    continue
                self.db.add(LogisticsHydrostaticTest(
                    cylinder_id=item.id,
                    test_date=idate(ph["Fecha_PH"]) or item.created_at.date(),
                    previous_test_date=idate(ph["Fecha_PH_Anterior"]),
                    status=clean(ph["Estado"]) or None,
                    notes=None,
                ))
                self.bump("hydro_tests")
            # servicios
            for s in read_csv("cilindros_servicios", ["id_cilindro_servicio", "cod_pedido", "id_detalle", "cod_movimiento", "cod_producto", "id_servicio", "estado_servicio", "fecha_inicio", "fecha_fin", "observaciones", "PcompraServicio", "PVentaServicio", "StkIngresoServicio", "StkEgreso", "CodGrupoServicio", "Porcentaje_desc", "Descuentoxitem", "Total_itemsServicio"]):
                if clean(s["cod_producto"]) != str(legacy_id):
                    continue
                self.db.add(LogisticsCylinderService(
                    cylinder_id=item.id,
                    service_type_id=str(service_type),
                    status=clean(s["estado_servicio"]) or "COMPLETADO",
                    start_date=idt(s["fecha_inicio"]),
                    end_date=idt(s["fecha_fin"]),
                    notes=clean(s["observaciones"]) or None,
                    purchase_price=num(s["PcompraServicio"]),
                    sale_price=num(s["PVentaServicio"]),
                    stock_in=num(s["StkIngresoServicio"]),
                    stock_out=num(s["StkEgreso"]),
                    created_by=self.created_by,
                ))
                self.bump("services")
        self._commit()

        # Estado log historico (por Serie = barcode2/Nro_Producto)
        cylinders_by_serial: dict[str, str] = {}
        for cyl in self.db.scalars(select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == self.tenant_id)).all():
            for key in (cyl.serial, cyl.barcode1, cyl.barcode2):
                if key:
                    cylinders_by_serial.setdefault(key, cyl.id)
        state_log_count = 0
        for log in read_csv("cilindro_estado_log", ["IdEstado", "Serie", "Estado", "Fecha", "Usuario", "Observacion", "Origen", "MotivoCodigo", "AlmacenId"]):
            cylinder_id = cylinders_by_serial.get(clean(log["Serie"]))
            if not cylinder_id:
                continue
            state = clean(log["Estado"]) or "EN_ALMACEN_VACIO"
            self.db.add(LogisticsCylinderStateLog(
                tenant_id=self.tenant_id,
                cylinder_id=cylinder_id, to_state=state, from_state=None,
                changed_by=self.created_by, origin=clean(log["Origen"]) or "LEGACY",
                reason_code=clean(log["MotivoCodigo"]) or None,
                notes=clean(log["Observacion"]) or None,
                created_at=idt(log["Fecha"]) or datetime.now(timezone.utc),
            ))
            state_log_count += 1
        self._commit()
        print(f"  cilindros OK: {self.counters.get('cylinders',0)} retimbrados={self.counters.get('retimbrados',0)} PH={self.counters.get('hydro_tests',0)} servicios={self.counters.get('services',0)} state_log={state_log_count}")
        self._fix_cylinder_gas_products()

    # ── Fase 8: emparejar cilindro -> gas (sublinea + capacidad/presion) ──
    def _fix_cylinder_gas_products(self) -> None:
        print("== Fase 8: emparejar cilindros con gas ==")
        import re

        product_fields = ["cod_producto", "Nro_Producto", "Desc_Producto", "StockMin_Producto", "Cod_Linea", "Cod_TipoInsumo", "Cod_Unidad", "Cod_UnidadCja", "Precio_Producto", "PrecioCja_Producto", "Costo_Producto", "peso_producto", "Marca_Producto", "Estado_Producto", "cIGV", "cant", "Cont", "cod_SubCategoria", "cod_grupo", "costo_total", "eliminar", "servicio", "barcode1", "barcode2", "stock", "lista2", "lista3", "lista4", "condicion", "M3", "ADR_Categoria", "ADR_TipoBulto", "ADR_PesoKg", "ADR_M3", "ADR_UN", "ADR_Mercancia", "ADR_Etiqueta", "ADR_Tunel", "ADR_Sublinea", "ADR_Factor", "ADR_Puntos", "ADR_UnidadMedida", "PaisCodigo"]
        gas_by_subline: dict[str, list[tuple[str, str, str]]] = {}  # subline -> [(product_id, Bn, presion)]
        group_by_gas: dict[str, str] = {}
        for row in read_csv("producto", product_fields):
            if clean(row["condicion"]) != "GAS":
                continue
            try:
                legacy_id = int(float(clean(row["cod_producto"])))
            except ValueError:
                continue
            product_id = self.map_product.get(legacy_id)
            if not product_id:
                continue
            subline = clean(row["Cod_Linea"])
            desc = clean(row["Desc_Producto"]) + " " + clean(row["Nro_Producto"])
            m = re.search(r"B(\d+)\s*/\s*(\d+)BAR", desc, re.IGNORECASE)
            cap, pres = (m.group(1), m.group(2)) if m else ("", "")
            gas_by_subline.setdefault(subline, []).append((product_id, cap, pres))
            group_by_gas[product_id] = clean(row["cod_grupo"])
        group_map: dict[str, str] = {}
        for row in read_csv("grupo", ["Cod_Grupo", "ID_ProductoGas", "CodBar_ProductoGas", "Desc_Grupo", "id_Categoria", "Categoria", "id_Linea", "Desc_Linea", "id_SubLinea", "Desc_SubLinea", "id_unidad", "Desc_unidad", "Precio1", "Precio2", "Precio3", "Precio4"]):
            try:
                gas_legacy = int(float(clean(row["ID_ProductoGas"])))
            except ValueError:
                continue
            gas_id = self.map_product.get(gas_legacy)
            if gas_id:
                group_map[gas_id] = self.map_group.get(clean(row["Cod_Grupo"]), "")
        fixed = unmatched = 0
        for cyl in self.db.scalars(select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == self.tenant_id, LogisticsCylinder.product_id.is_(None))).all():
            row = None
            for r in read_csv("producto", product_fields):
                if clean(r["barcode2"]) == cyl.serial or clean(r["barcode1"]) == cyl.serial or clean(r["Nro_Producto"]) == cyl.serial:
                    row = r
                    break
            if row is None:
                unmatched += 1
                continue
            subline = clean(row["Cod_Linea"])
            desc = clean(row["Desc_Producto"])
            m = re.search(r"B(\d+)\s*/\s*(\d+)BAR", desc, re.IGNORECASE)
            cap, pres = (m.group(1), m.group(2)) if m else ("", "")
            candidates = gas_by_subline.get(subline, [])
            match = None
            for pid, gcap, gpres in candidates:
                if gcap == cap and gpres == pres:
                    match = pid
                    break
            if match is None and cap:
                for pid, gcap, gpres in candidates:
                    if gcap == cap:
                        match = pid
                        break
            if match is None and len(candidates) == 1:
                match = candidates[0][0]
            if match is None:
                unmatched += 1
                continue
            cyl.product_id = match
            cyl.gas_group_id = group_map.get(match) or self.map_group.get(clean(row["cod_grupo"]))
            self.db.add(cyl)
            fixed += 1
        self._commit()
        print(f"  emparejados: {fixed}, sin match: {unmatched}")


def main() -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    with session_factory() as db:

        tenant_row = db.execute(text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")).scalar_one()
        branch_row = db.execute(text("SELECT id FROM branches ORDER BY created_at LIMIT 1")).scalar_one()
        user_row = db.execute(text("SELECT id FROM users ORDER BY created_at LIMIT 1")).scalar_one()
        imp = Importer(db, tenant_id=str(tenant_row), branch_id=str(branch_row), user_id=str(user_row))
        print(f"tenant={tenant_row} branch={branch_row} user={user_row} dry_run={DRY_RUN}")
        imp.catalogs()
        imp.warehouses()
        imp.products()
        imp.groups()
        imp.adr()
        imp.customers()
        imp.delivery_points()
        imp.cylinders()
        imp.stock()
        print("== RESUMEN ==")
        for key, value in sorted(imp.counters.items()):
            print(f"  {key}: {value}")
        if DRY_RUN:
            db.rollback()
            print("(dry-run: nada persistido)")


if __name__ == "__main__":
    main()
