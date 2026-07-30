"""
Seed masivo de datos demo: 600 productos, 3000 envases, 100 clientes.

Uso: python -m apps.api.app.commands.seed_massive
"""

from __future__ import annotations

import hashlib
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.config import Settings
from apps.api.app.core.database import build_engine, build_session_factory
from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry
from plugins.crm.backend.models import (
    CrmCustomer,
    CrmCustomerAddress,
    CrmCustomerBankAccount,
    CrmCustomerContact,
    CrmPaymentTerm,
)
from plugins.logistics.backend.models import (
    LogisticsContractType,
    LogisticsCylinder,
    LogisticsCylinderOwnership,
    LogisticsCylinderStateLog,
    LogisticsCylinderContract,
    LogisticsCustomerCylinderLedger,
    LogisticsDeliveryPoint,
    LogisticsLoadPlan,
    LogisticsLoadPlanItem,
    LogisticsLoadSerialAssignment,
    LogisticsMovementType,
    LogisticsPlanningReservation,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.ventas.cotizacion.backend.models import QuoteDraft, QuoteItem
from plugins.productos.backend.models import (
    Product,
    ProductAdr,
    ProductBrand,
    ProductCategory,
    ProductCost,
    ProductLine,
    ProductPrice,
    ProductSubline,
    ProductUnit,
)
from plugins.stock.backend.models import StockBalance, StockConfig, StockLedger

# ── Utility ──────────────────────────────────────────────────────────

def new_id() -> str:
    """Generate a valid UUID v4 without importing uuid."""
    import uuid
    return str(uuid.uuid4())


def random_dni() -> str:
    return "".join(random.choices("0123456789", k=8))


def random_ruc() -> str:
    return "20" + "".join(random.choices("0123456789", k=9))


def random_iban() -> str:
    return "ES" + "".join(random.choices("0123456789", k=22))


def random_phone() -> str:
    return "+51 " + "".join(random.choices("0123456789", k=9))


def random_email(legal_name: str) -> str:
    slug = legal_name.lower().replace(" ", ".").replace(",", "")[:20]
    return f"{slug}@demo.com"


def pick_one(items: list) -> object:
    return random.choice(items)


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ── Product catalog ──────────────────────────────────────────────────

GAS_PRODUCTS = [
    ("GLP10", "Bombona 10 kg GLP", 10.0, 10.0, 45.0),
    ("GLP15", "Bombona 15 kg GLP", 15.0, 15.0, 67.0),
    ("GLP45", "Bombona 45 kg GLP", 45.0, 45.0, 180.0),
    ("OXI6", "Oxígeno 6 m³", 6.0, 0.0, 30.0),
    ("OXI10", "Oxígeno 10 m³", 10.0, 0.0, 50.0),
    ("NIT6", "Nitrógeno 6 m³", 6.0, 0.0, 35.0),
    ("NIT10", "Nitrógeno 10 m³", 10.0, 0.0, 55.0),
    ("ACE6", "Acetileno 6 kg", 6.0, 0.0, 80.0),
    ("ACE3", "Acetileno 3 kg", 3.0, 0.0, 45.0),
    ("CO2_10", "CO2 10 kg", 10.0, 0.0, 40.0),
    ("CO2_20", "CO2 20 kg", 20.0, 0.0, 70.0),
    ("ARG10", "Argón 10 m³", 10.0, 0.0, 60.0),
    ("ARG20", "Argón 20 m³", 20.0, 0.0, 110.0),
    ("HEL5", "Helio 5 m³", 5.0, 0.0, 90.0),
    ("HEL10", "Helio 10 m³", 10.0, 0.0, 170.0),
    ("HID6", "Hidrógeno 6 m³", 6.0, 0.0, 55.0),
    ("HID12", "Hidrógeno 12 m³", 12.0, 0.0, 100.0),
    ("PROP10", "Propano 10 kg", 10.0, 10.0, 50.0),
    ("PROP45", "Propano 45 kg", 45.0, 45.0, 190.0),
    ("BUT12", "Butano 12.5 kg", 12.5, 12.5, 55.0),
]

CYLINDER_TYPES = [
    ("CIL-10KG", "Cilindro 10 kg", 10, "Soldadura", 18.0),
    ("CIL-15KG", "Cilindro 15 kg", 15, "Soldadura", 22.0),
    ("CIL-45KG", "Cilindro 45 kg", 45, "Industrial", 55.0),
    ("CIL-6M3", "Cilindro 6 m³", 6, "Alta presión", 40.0),
    ("CIL-10M3", "Cilindro 10 m³", 10, "Alta presión", 50.0),
    ("CIL-ACET", "Cilindro acetileno", 6, "Acetileno", 35.0),
    ("CIL-ARG", "Cilindro argón", 10, "Alta presión", 55.0),
    ("CIL-HEL", "Cilindro helio", 5, "Alta presión", 60.0),
    ("CIL-CO2", "Cilindro CO2", 10, "Refrigeración", 30.0),
    ("CIL-20M3", "Cilindro 20 m³", 20, "Alta presión", 75.0),
]

SERVICE_PRODUCTS = [
    ("SRV-RETIM", "Retimbrado de cilindro", 15.0),
    ("SRV-PINT", "Pintado de cilindro", 25.0),
    ("SRV-GRIFO", "Cambio de grifo/válvula", 35.0),
    ("SRV-HIDRO", "Prueba hidrostática", 50.0),
    ("SRV-TRANS", "Transporte y flete", 80.0),
    ("SRV-MANT", "Mantenimiento general", 40.0),
    ("SRV-INST", "Instalación de red", 200.0),
    ("SRV-ASIS", "Asistencia técnica", 60.0),
    ("SRV-CERT", "Certificación de envases", 30.0),
    ("SRV-CARGA", "Recarga express", 20.0),
]

ACCESSORY_PRODUCTS = [
    ("ACC-MAN", "Manómetro 0-200 bar", 45.0),
    ("ACC-REG", "Regulador de presión", 65.0),
    ("ACC-MAN2", "Manorreductor", 85.0),
    ("ACC-MANG", "Manguera 5m alta presión", 25.0),
    ("ACC-MANG10", "Manguera 10m alta presión", 45.0),
    ("ACC-SOPLE", "Soplete corte", 120.0),
    ("ACC-SOPLE2", "Soplete calentamiento", 95.0),
    ("ACC-ANTI", "Válvula antirretorno", 30.0),
    ("ACC-CAPU", "Capuchón protector", 8.0),
    ("ACC-CARR", "Carro portacilindros", 150.0),
    ("ACC-LLAVE", "Llave de cilindro universal", 18.0),
    ("ACC-SELLO", "Sello de seguridad", 3.0),
]

# ── Customer data ────────────────────────────────────────────────────

PERUVIAN_CITIES = [
    "Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura",
    "Cusco", "Huancayo", "Iquitos", "Tacna", "Puno",
    "Ica", "Cajamarca", "Ayacucho", "Juliaca", "Chimbote",
]

PERUVIAN_COMPANIES = [
    "Constructora Los Andes SAC",
    "Metalúrgica del Sur SA",
    "Soldaduras Peruanas EIRL",
    "Fábrica de Estructuras Metálicas del Norte SAC",
    "Hospital Regional Centro",
    "Clínica San Pablo SA",
    "Laboratorios Farmacéuticos Andinos SAC",
    "Industrias Químicas del Pacífico SA",
    "Taller Mecánico Industrial Rodríguez EIRL",
    "Carpintería Metálica La Unión SAC",
    "Ferretería El Soldador SAC",
    "Distribuidora de Gases del Perú SA",
    "Refrigeración Industrial Costera EIRL",
    "Astillero Naval del Callao SAC",
    "Minería y Construcción Los Andes SA",
    "Empresa de Transportes San Cristóbal SAC",
    "Agroindustrias del Valle SA",
    "Procesadora de Alimentos Andinos EIRL",
    "Textil Peruana del Sur SAC",
    "Plásticos Industriales del Perú SA",
]

PERUVIAN_FIRST = [
    "Juan", "María", "Carlos", "Rosa", "Luis", "Ana", "Pedro",
    "Carmen", "José", "Gloria", "Miguel", "Lucía", "Jorge", "Elena",
    "Víctor", "Patricia", "Oscar", "Diana", "Alberto", "Sandra",
]

PERUVIAN_LAST = [
    "García", "Rodríguez", "López", "Martínez", "González",
    "Pérez", "Sánchez", "Ramírez", "Torres", "Flores",
    "Rivera", "Cruz", "Morales", "Ortiz", "Gutiérrez",
    "Chávez", "Ramos", "Vargas", "Castillo", "Reyes",
]

ADDRESSES = [
    "Av. Industrial 1234", "Jr. Comercio 567", "Calle Las Palmeras 890",
    "Av. Los Olivos 234", "Jr. Arequipa 456", "Calle Real 789",
    "Av. Universitaria 3456", "Carretera Central km 12", "Zona Industrial Lote 5",
    "Av. La Marina 678", "Jr. Huancavelica 901", "Calle Los Pinos 234",
    "Av. Argentina 5678", "Panamericana Sur km 25", "Parque Industrial Mz A Lt 3",
    "Av. Colonial 123", "Jr. Lima 456", "Calle Comercio 789",
    "Av. Brasil 2345", "Jr. Moquegua 890", "Calle San Martín 123",
]

# ── Seed functions ───────────────────────────────────────────────────

def seed_catalogs(db: Session, tenant_id: str) -> dict:
    """Create the product catalog hierarchy."""
    categories = []
    lines = {}
    sublines = {}
    brands = {}
    units = {}

    cat_names = [
        ("GASES", "Gases industriales y medicinales"),
        ("ENVASES", "Cilindros y envases"),
        ("SERVICIOS", "Servicios técnicos"),
        ("ACCESORIOS", "Accesorios y repuestos"),
    ]
    for code, name in cat_names:
        cat = ProductCategory(code=code, name=name, description=name, tenant_id=tenant_id)
        db.add(cat)
        db.flush()
        categories.append(cat)

    line_defs = [
        ("GLP", "Gas Licuado de Petróleo", categories[0]),
        ("AIRE", "Gases del Aire", categories[0]),
        ("REFRIG", "Gases Refrigerantes", categories[0]),
        ("ESPECIALES", "Gases Especiales", categories[0]),
        ("MEDICINAL", "Gases Medicinales", categories[0]),
        ("CILINDROS", "Envases a Presión", categories[1]),
        ("TECNICO", "Servicios Técnicos", categories[2]),
        ("INSTALACION", "Instalaciones", categories[2]),
        ("SEGURIDAD", "Accesorios de Seguridad", categories[3]),
        ("HERRAMIENTAS", "Herramientas", categories[3]),
    ]
    for code, name, cat in line_defs:
        line = ProductLine(code=code, name=name, category_id=cat.id, tenant_id=tenant_id)
        db.add(line)
        db.flush()
        lines[code] = line

    subline_defs = [
        ("COMBUSTIBLE", "Combustible", lines["GLP"]),
        ("OXIGENO", "Oxígeno", lines["AIRE"]),
        ("NITROGENO", "Nitrógeno", lines["AIRE"]),
        ("ARGON", "Argón", lines["AIRE"]),
        ("ACETILENO", "Acetileno", lines["ESPECIALES"]),
        ("HELIO", "Helio", lines["ESPECIALES"]),
        ("HIDROGENO", "Hidrógeno", lines["ESPECIALES"]),
        ("CO2", "Dióxido de Carbono", lines["REFRIG"]),
        ("PROPANO", "Propano", lines["GLP"]),
        ("BUTANO", "Butano", lines["GLP"]),
        ("MED_OXIGENO", "Oxígeno Medicinal", lines["MEDICINAL"]),
        ("CIL_SOLD", "Cilindros Soldadura", lines["CILINDROS"]),
        ("CIL_AP", "Cilindros Alta Presión", lines["CILINDROS"]),
        ("CIL_IND", "Cilindros Industriales", lines["CILINDROS"]),
        ("REPARACION", "Reparación", lines["TECNICO"]),
        ("MANTENIMIENTO", "Mantenimiento", lines["TECNICO"]),
        ("INST_RED", "Instalación Redes", lines["INSTALACION"]),
        ("VALVULAS", "Válvulas", lines["SEGURIDAD"]),
        ("MANOMETROS", "Manómetros", lines["HERRAMIENTAS"]),
    ]
    for code, name, line in subline_defs:
        sub = ProductSubline(code=code, name=name, line_id=line.id, tenant_id=tenant_id)
        db.add(sub)
        db.flush()
        sublines[code] = sub

    brand_names = [
        "Linde", "Praxair", "Air Products", "Messer", "ACA",
        "CilindrosPerú", "EnvaPerú", "GasAndino", "SoldaSur", "InduGas",
    ]
    for name in brand_names:
        code = name.upper().replace(" ", "_")[:20]
        brand = ProductBrand(code=code, name=name, description=f"Marca {name}", tenant_id=tenant_id)
        db.add(brand)
        db.flush()
        brands[name] = brand

    unit_defs = [
        ("KG", "Kilogramo", None, None, None, 1.0),
        ("M3", "Metro cúbico", None, None, None, None),
        ("UN", "Unidad", 1, None, None, None),
        ("L", "Litro", None, 1.0, None, None),
        ("MT", "Metro", None, None, None, None),
    ]
    for code, name, eq, m3, ltr, kg in unit_defs:
        unit = ProductUnit(code=code, name=name, equivalencia=eq, m3_factor=m3,
                           liter_factor=ltr, kg_factor=kg, tenant_id=tenant_id)
        db.add(unit)
        db.flush()
        units[code] = unit

    # Ensure movement types exist (may be wiped by TRUNCATE CASCADE)
    from plugins.logistics.backend.services.catalog import MOVEMENT_TYPE_DEFINITIONS

    existing_mt = {row.code for row in db.scalars(
        select(LogisticsMovementType.code)
    ).all()}
    for code, name, category, moves_cylinders, origin_state, target_state in MOVEMENT_TYPE_DEFINITIONS:
        if code not in existing_mt:
            db.add(LogisticsMovementType(
                code=code, name=name, category=category,
                moves_cylinders=moves_cylinders,
                origin_state=origin_state, target_state=target_state,
            ))
    if any(code not in existing_mt for code, *_ in MOVEMENT_TYPE_DEFINITIONS):
        db.flush()

    db.commit()
    return {"categories": categories, "lines": lines, "sublines": sublines,
            "brands": brands, "units": units}


def seed_products(db: Session, tenant_id: str, user_id: str, catalogs: dict) -> list:
    """Create 600+ products with prices, costs, and ADR."""
    products = []
    lines = catalogs["lines"]
    sublines = catalogs["sublines"]
    brands = catalogs["brands"]
    units = catalogs["units"]
    brand_list = list(brands.values())

    # ── Gas products (core, 20) ──
    for i, (sku, name, weight, default_weight, price) in enumerate(GAS_PRODUCTS):
        sub = sublines.get(_gas_subline(sku), sublines["COMBUSTIBLE"])
        line = sub.line_id  # type: ignore[attr-defined]
        product = Product(
            id=new_id(), tenant_id=tenant_id,
            sku=sku, name=name, description=name,
            line_id=_resolve_line_id(line, lines),
            subline_id=sub.id,
            brand_id=pick_one(brand_list).id,
            unit_id=units["KG"].id,
            status_code="ACTIVO", condition_code="GAS",
            weight_kg=weight, default_weight_kg=default_weight,
            country_code="PER", is_service=False, is_active=True,
                created_by=user_id,
        )
        db.add(product)
        db.flush()
        products.append(product)

        _add_price(db, product.id, tenant_id, user_id, "BASE", price)
        _add_cost(db, product.id, tenant_id, user_id, "BASE", price * 0.6)
        _add_adr(db, product.id, tenant_id, user_id, weight)

        # Variants with different sizes
        variants = [
            (f"{sku}-IND", f"{name} (Industrial)", price * 0.9),
            (f"{sku}-MED", f"{name} (Medicinal)", price * 1.5),
            (f"{sku}-ALTA", f"{name} (Alta Pureza)", price * 2.0),
        ]
        for v_sku, v_name, v_price in variants:
            vp = Product(
                id=new_id(), tenant_id=tenant_id,
                sku=v_sku, name=v_name, description=v_name,
                line_id=_resolve_line_id(line, lines),
                subline_id=sub.id,
                brand_id=pick_one(brand_list).id,
                unit_id=units["KG"].id,
                status_code="ACTIVO", condition_code="GAS",
                weight_kg=weight, default_weight_kg=default_weight,
                is_active=random.choice([True, True, True, False]),
                created_by=user_id,
            )
            db.add(vp)
            db.flush()
            products.append(vp)
            _add_price(db, vp.id, tenant_id, user_id, "BASE", v_price)
            _add_cost(db, vp.id, tenant_id, user_id, "BASE", v_price * 0.55)
            _add_adr(db, vp.id, tenant_id, user_id, weight)

    # ── Cylinder products (40) ──
    for i, (sku, name, capacity, desc, cost_price) in enumerate(CYLINDER_TYPES):
        sub = sublines["CIL_SOLD"]
        product = Product(
            id=new_id(), tenant_id=tenant_id,
            sku=sku, name=name, description=f"{name} - {desc}",
            line_id=lines["CILINDROS"].id, subline_id=sub.id,
            brand_id=pick_one(brand_list).id,
            unit_id=units["UN"].id,
            status_code="ACTIVO", condition_code="CILPRO",
            weight_kg=float(capacity), default_weight_kg=float(capacity),
            is_service=False, is_active=True,
                created_by=user_id,
        )
        db.add(product)
        db.flush()
        products.append(product)
        _add_price(db, product.id, tenant_id, user_id, "BASE", cost_price * 2.8)
        _add_cost(db, product.id, tenant_id, user_id, "BASE", cost_price)

        # 3 variants per cylinder type
        for j in range(3):
            vs = Product(
                id=new_id(), tenant_id=tenant_id,
                sku=f"{sku}-V{j+1}", name=f"{name} (Reforzado V{j+1})",
                line_id=lines["CILINDROS"].id, subline_id=sub.id,
                brand_id=pick_one(brand_list).id,
                unit_id=units["UN"].id,
                status_code="ACTIVO", condition_code="CILPRO",
                weight_kg=float(capacity + 2), default_weight_kg=float(capacity + 2),
            is_active=True,
                created_by=user_id,
        )
            db.add(vs)
            db.flush()
            products.append(vs)
            _add_price(db, vs.id, tenant_id, user_id, "BASE", cost_price * 1.5 * (j + 2))
            _add_cost(db, vs.id, tenant_id, user_id, "BASE", cost_price * (j + 1.5))

    # ── Service products (10 + variants) ──
    for sku, name, price in SERVICE_PRODUCTS:
        sub = sublines["REPARACION"]
        product = Product(
            id=new_id(), tenant_id=tenant_id,
            sku=sku, name=name, description=name,
            line_id=lines["TECNICO"].id, subline_id=sub.id,
            brand_id=pick_one(brand_list).id,
            unit_id=units["UN"].id,
            status_code="ACTIVO", condition_code="SERVICIO",
            is_service=True, is_active=True,
                            created_by=user_id,
        )
        db.add(product)
        db.flush()
        products.append(product)
        _add_price(db, product.id, tenant_id, user_id, "BASE", price)
        _add_cost(db, product.id, tenant_id, user_id, "BASE", price * 0.3)

    # ── Accessory products (12 + variants) ──
    for sku, name, price in ACCESSORY_PRODUCTS:
        product = Product(
            id=new_id(), tenant_id=tenant_id,
            sku=sku, name=name, description=name,
            line_id=lines["HERRAMIENTAS"].id,
            subline_id=sublines["MANOMETROS"].id,
            brand_id=pick_one(brand_list).id,
            unit_id=units["UN"].id,
            status_code="ACTIVO", condition_code="PRODUCTO",
            is_active=True,
                            created_by=user_id,
        )
        db.add(product)
        db.flush()
        products.append(product)
        _add_price(db, product.id, tenant_id, user_id, "BASE", price)
        _add_cost(db, product.id, tenant_id, user_id, "BASE", price * 0.45)

    # ── Gas blend variants (fill to 600) ──
    needed = 600 - len(products)
    special_gases = [
        "Mezcla Argón-CO2", "Mezcla Argón-Oxígeno", "Mezcla Argón-Helio",
        "Mezcla Nitrógeno-Hidrógeno", "Aire Sintético", "Gas de Protección MIG",
        "Gas de Protección TIG", "Gas de Calibración", "Gas Carrier",
        "Gas de Purga", "Gas Inerte", "Gas de Formación",
    ]
    for i in range(needed):
        gas_name = random.choice(special_gases)
        conc = random.choice(["5%", "10%", "20%", "30%", "50%", "75%"])
        name = f"{gas_name} {conc}"
        sku = f"MEZ-{i:04d}"
        sub = random.choice(list(sublines.values()))
        product = Product(
            id=new_id(), tenant_id=tenant_id,
            sku=sku, name=name, description=name,
            line_id=_resolve_line_id(sub.line_id, lines),
            subline_id=sub.id,
            brand_id=pick_one(brand_list).id,
            unit_id=units["M3"].id,
            status_code="ACTIVO", condition_code="GAS",
            weight_kg=random.uniform(1, 50),
            is_active=random.choice([True, True, False]),
                created_by=user_id,
        )
        db.add(product)
        db.flush()
        products.append(product)
        _add_price(db, product.id, tenant_id, user_id, "BASE", round(random.uniform(30, 300), 2))
        _add_cost(db, product.id, tenant_id, user_id, "BASE", round(random.uniform(15, 150), 2))

    db.commit()
    return products


def _gas_subline(sku: str) -> str:
    mapping = {
        "GLP": "COMBUSTIBLE", "OXI": "OXIGENO", "NIT": "NITROGENO",
        "ACE": "ACETILENO", "CO2": "CO2", "ARG": "ARGON",
        "HEL": "HELIO", "HID": "HIDROGENO", "PROP": "PROPANO", "BUT": "BUTANO",
    }
    for prefix, subline in mapping.items():
        if sku.startswith(prefix):
            return subline
    return "COMBUSTIBLE"


def _resolve_line_id(line_id, lines):
    if isinstance(line_id, str):
        return lines[line_id].id if line_id in lines else next(iter(lines.values())).id
    return line_id


def _add_price(db, product_id, tenant_id, user_id, price_list, amount):
    p = ProductPrice(
        id=new_id(), tenant_id=tenant_id, product_id=product_id,
        price_list=price_list, amount=amount, valid_from=date(2026, 1, 1),
        currency="PEN", created_by=user_id,
    )
    db.add(p)


def _add_cost(db, product_id, tenant_id, user_id, cost_type, amount):
    c = ProductCost(
        id=new_id(), tenant_id=tenant_id, product_id=product_id,
        cost_type=cost_type, amount=amount, valid_from=date(2026, 1, 1),
        currency="PEN", created_by=user_id,
    )
    db.add(c)


def _add_adr(db, product_id, tenant_id, user_id, weight):
    a = ProductAdr(
        id=new_id(), tenant_id=tenant_id, product_id=product_id,
        category="2F", un_number="1075", packaging_type="CIL",
        net_weight_kg=weight, cargo_description="Gas licuado de petróleo",
        label="GLP", tunnel_restriction="B/D",
        factor=1, points=3, unit_measure="KG",
        valid_from=date(2026, 1, 1), created_by=user_id,
    )
    db.add(a)


# ── Customers ────────────────────────────────────────────────────────

def seed_customers(db: Session, tenant_id: str, user_id: str) -> list:
    """Create 100 customers with addresses, contacts, and bank accounts."""
    payment_terms = db.execute(select(CrmPaymentTerm)).scalars().all()
    customers = []

    company_count = len(PERUVIAN_COMPANIES)
    for i in range(100):
        if i < company_count:
            doc_type = "RUC"
            doc_number = random_ruc()
            legal_name = PERUVIAN_COMPANIES[i]
            commercial_name = legal_name.replace(" SAC", "").replace(" SA", "").replace(" EIRL", "")
        else:
            doc_type = "DNI"
            doc_number = random_dni()
            first = random.choice(PERUVIAN_FIRST)
            last = f"{random.choice(PERUVIAN_LAST)} {random.choice(PERUVIAN_LAST)}"
            legal_name = f"{first} {last}"
            commercial_name = legal_name

        city = random.choice(PERUVIAN_CITIES)
        pt = pick_one(payment_terms)

        customer = CrmCustomer(
            id=new_id(), tenant_id=tenant_id,
            legal_name=legal_name, commercial_name=commercial_name,
            document_type_code=doc_type, document_number=doc_number,
            country_code="PER",
            email=random_email(legal_name),
            phone=random_phone(),
            payment_term_code=pt.code,
            billing_type=random.choice(["por_operacion", "mensual", "por_operacion"]),
            is_exempt=random.choice([True, False, False, False, False]),
            accounting_code=f"C{201000 + i:06d}",
            is_intracommunity=False,
            created_by=user_id,
        )
        db.add(customer)
        db.flush()

        addr = CrmCustomerAddress(
            id=new_id(), tenant_id=tenant_id, customer_id=customer.id,
            address_type="FISCAL", line1=random.choice(ADDRESSES),
            city=city, state=city, country_code="PER",
        )
        db.add(addr)

        if i < 20:
            for atype in ("ENTREGA", "COMERCIAL"):
                addr2 = CrmCustomerAddress(
                    id=new_id(), tenant_id=tenant_id, customer_id=customer.id,
                    address_type=atype, line1=random.choice(ADDRESSES),
                    city=city, state=city, country_code="PER",
                )
                db.add(addr2)

        contact = CrmCustomerContact(
            id=new_id(), tenant_id=tenant_id, customer_id=customer.id,
            full_name=f"{random.choice(PERUVIAN_FIRST)} {random.choice(PERUVIAN_LAST)}",
            role=random.choice(["Gerente", "Jefe de Planta", "Comprador", "Administrador", "Dueño"]),
            phone=random_phone(), email=random_email(legal_name),
            contact_type="GENERAL",
        )
        db.add(contact)

        bank = CrmCustomerBankAccount(
            id=new_id(), tenant_id=tenant_id, customer_id=customer.id,
            bank_name=random.choice(["BCP", "BBVA", "Interbank", "Scotiabank", "BanBif"]),
            account_holder=legal_name,
            iban=random_iban(),
            is_primary=True, is_active=True,
        )
        db.add(bank)

        customers.append(customer)

    db.commit()
    return customers


# ── Cylinders ────────────────────────────────────────────────────────

def seed_cylinders(
    db: Session,
    tenant_id: str,
    user_id: str,
    products: list,
    warehouses: list,
    customers: list | None = None,
    sessions: list | None = None,
) -> list:
    """Create 3000 cylinders. Transit cylinders assigned to active sessions."""
    gas_products = [p for p in products if p.condition_code == "GAS" and p.weight_kg and p.weight_kg > 0]
    cylinder_products = [p for p in products if p.condition_code == "CILPRO"]
    cylinders = []
    active_sessions = [s for s in (sessions or []) if s.status in ("LOADING", "OUTBOUND")]

    if not gas_products:
        gas_products = products[:10]
    if not cylinder_products:
        cylinder_products = products[:5]

    state_dist = (
        ["EN_ALMACEN_VACIO"] * 60
        + ["EN_CLIENTE_LLENO"] * 10 + ["EN_CLIENTE_VACIO"] * 10
        + ["EN_RUTA"] * 5 + ["CARGA_EN_VEHICULO"] * 5
        + ["LLENADO_OK"] * 5
        + ["EN_MANTENIMIENTO"] * 2 + ["BLOQUEADO"] * 1
        + ["DE_BAJA"] * 1 + ["OBSERVADO"] * 1
    )

    serial_prefixes = ["GL", "OX", "NI", "AC", "AR", "HE", "HI", "CO", "PR", "BU"]

    for i in range(3000):
        prefix = serial_prefixes[i % len(serial_prefixes)]
        serial = f"{prefix}-{i+1:06d}"
        state = state_dist[i % len(state_dist)]

        cylinder_product = pick_one(cylinder_products)
        gas_product = pick_one(gas_products)
        warehouse = pick_one(warehouses) if warehouses else None

        session_id = None
        location = warehouse.name if warehouse else "Sin ubicación"
        customer = None
        if state in ("CARGA_EN_VEHICULO", "EN_RUTA") and active_sessions:
            sess = pick_one(active_sessions)
            session_id = sess.id
            location = f"Móvil {sess.id[:8]}"

        if state in ("EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO") and customers:
            customer = pick_one(customers)
            location = customer.legal_name

        hydro_date = random_date(date(2020, 1, 1), date(2025, 12, 31))
        next_hydro = hydro_date + timedelta(days=5 * 365 + random.randint(0, 180))

        cyl = LogisticsCylinder(
            id=new_id(), tenant_id=tenant_id,
            serial=serial,
            current_state=state,
            session_id=session_id,
            product_id=gas_product.id,
            branch_id=warehouse.branch_id if warehouse else None,
            location=location,
            content_kg=gas_product.weight_kg,
            weight_origin=cylinder_product.weight_kg or 10.0,
            weight_current=cylinder_product.weight_kg or 10.0,
            condition=cylinder_product.condition_code,
            brand_id=cylinder_product.brand_id,
            last_hydrotest_date=hydro_date,
            next_hydrotest_date=next_hydro,
            manufacturer_date=hydro_date - timedelta(days=random.randint(365, 1825)),
            adr_category="2F",
            adr_un_number="1075",
            adr_label="GLP",
            adr_package_type="CIL",
            adr_weight_kg=gas_product.weight_kg or 10.0,
            adr_merchandise=gas_product.name,
            adr_tunnel="B/D",
            is_active=state not in ("DE_BAJA", "BLOQUEADO"),
            is_medical=random.choice([True, False, False, False]),
        )
        db.add(cyl)
        cylinders.append(cyl)
        if customer is not None:
            db.add(
                LogisticsCylinderOwnership(
                    id=new_id(),
                    cylinder_id=cyl.id,
                    customer_id=customer.id,
                    customer_name=customer.legal_name,
                    condition=cyl.condition,
                    notes="seed_massive: estado cliente",
                    created_by=user_id,
                )
            )
            db.add(
                LogisticsCustomerCylinderLedger(
                    id=new_id(),
                    tenant_id=tenant_id,
                    customer_id=customer.id,
                    source_type="SEED_MASSIVE",
                    source_id=cyl.id,
                    event_type="IN_TO_CUSTOMER",
                    product_id=cyl.product_id,
                    product_name=gas_product.name,
                    condition=cyl.condition,
                    quantity=1,
                    cylinder_id=cyl.id,
                    trace_mode="SERIALIZED",
                    occurred_at=datetime.now(UTC),
                    created_by=user_id,
                    notes="seed_massive: estado cliente",
                )
            )
            db.add(
                LogisticsCylinderStateLog(
                    tenant_id=tenant_id,
                    cylinder_id=cyl.id,
                    from_state=None,
                    to_state=state,
                    changed_by=user_id,
                    origin="SEED_MASSIVE",
                    notes="seed_massive: estado cliente",
                )
            )

        if i % 500 == 0:
            db.flush()

    db.commit()
    return cylinders


# ── Load Serial Assignments ────────────────────────────────────────────

def seed_load_serial_assignments(
    db: Session,
    tenant_id: str,
    user_id: str,
    sessions: list,
) -> None:
    """Assign real cylinders to load plan items, adjusting quantities to reality."""
    active_sessions = [s for s in sessions if s.status in ("LOADING", "OUTBOUND")]
    for session in active_sessions:
        items = list(db.scalars(
            select(LogisticsLoadPlanItem).join(LogisticsLoadPlan).where(
                LogisticsLoadPlan.session_id == session.id,
            )
        ).all())
        for item in items:
            available = list(db.scalars(
                select(LogisticsCylinder).where(
                    LogisticsCylinder.tenant_id == tenant_id,
                    LogisticsCylinder.product_id == item.product_id,
                    LogisticsCylinder.is_active.is_(True),
                    LogisticsCylinder.session_id.is_(None),
                    LogisticsCylinder.current_state.in_(("LLENADO_OK", "EN_ALMACEN_VACIO")),
                ).limit(100)
            ).all())
            if not available:
                item.planned_quantity = 0
                db.add(item)
                continue

            real_qty = min(len(available), int(item.planned_quantity), 20)
            item.planned_quantity = real_qty
            db.add(item)

            for i in range(real_qty):
                cylinder = available[i]
                assignment_status = (
                    "CONFIRMED" if session.status == "OUTBOUND" else "SELECTED"
                )
                db.add(LogisticsLoadSerialAssignment(
                    id=new_id(),
                    tenant_id=tenant_id,
                    session_id=session.id,
                    product_id=item.product_id,
                    cylinder_id=cylinder.id,
                    cylinder_serial=cylinder.serial,
                    assignment_status=assignment_status,
                    selected_by=user_id,
                    selected_at=datetime.now(UTC),
                ))
                cylinder.session_id = session.id
                if session.status == "OUTBOUND" and cylinder.current_state not in (
                    "CARGA_EN_VEHICULO", "EN_RUTA"
                ):
                    cylinder.current_state = "CARGA_EN_VEHICULO"
                db.add(cylinder)

    db.commit()


def _repair_seed_customer_for_session(
    db: Session, *, session_id: str | None
) -> str | None:
    if session_id is None:
        return None
    session = db.scalar(
        select(LogisticsVehicleSession).where(LogisticsVehicleSession.id == session_id)
    )
    if session is None or session.route_id is None:
        return None
    customer_ids = [
        row[0]
        for row in db.execute(
            select(LogisticsDeliveryPoint.customer_id)
            .join(
                LogisticsRouteStop,
                LogisticsRouteStop.delivery_point_id == LogisticsDeliveryPoint.id,
            )
            .where(
                LogisticsRouteStop.route_id == session.route_id,
                LogisticsDeliveryPoint.customer_id.is_not(None),
            )
            .distinct()
        ).all()
        if row[0] is not None
    ]
    if len(customer_ids) == 1:
        return customer_ids[0]
    return None


def _repair_seed_customer_for_contract(
    db: Session,
    *,
    product_id: str | None,
    condition: str | None,
) -> str | None:
    if product_id is None:
        return None
    customer_ids = [
        row[0]
        for row in db.execute(
            select(LogisticsCylinderContract.customer_id)
            .where(
                LogisticsCylinderContract.status == "ACTIVE",
                LogisticsCylinderContract.cylinder_type_id == product_id,
                LogisticsCylinderContract.cylinder_condition == condition,
            )
            .distinct()
        ).all()
        if row[0] is not None
    ]
    if len(customer_ids) == 1:
        return customer_ids[0]
    return None


def _pick_seed_fallback_customer(cylinder_id: str, customers: list[CrmCustomer]) -> CrmCustomer:
    digest = hashlib.md5(cylinder_id.encode("utf-8"), usedforsecurity=False).hexdigest()
    index = int(digest, 16) % len(customers)
    return customers[index]


def repair_seed_customer_possession_orphans(
    db: Session,
    tenant_id: str,
    user_id: str,
    customers: list[CrmCustomer],
    *,
    env: str = "local",
    allow_fallback: bool = False,
) -> dict[str, int]:
    stats = {
        "resolved_by_session": 0,
        "resolved_by_contract": 0,
        "resolved_by_fallback": 0,
        "skipped_repaired": 0,
        "state_logs_created": 0,
        "ledgers_created": 0,
        "ownerships_created": 0,
        "session_links_cleared": 0,
        "not_repairable": 0,
        "unresolved": 0,
    }
    if not customers:
        return stats

    fallback_allowed = env in {"local", "development", "test"} or allow_fallback

    orphan_cylinders = list(
        db.scalars(
            select(LogisticsCylinder).where(
                LogisticsCylinder.tenant_id == tenant_id,
                LogisticsCylinder.current_state.in_(("EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO")),
                (
                    ~select(LogisticsCylinderOwnership.id)
                    .where(LogisticsCylinderOwnership.cylinder_id == LogisticsCylinder.id)
                    .exists()
                )
                |
                select(LogisticsCylinderOwnership.id)
                .where(
                    LogisticsCylinderOwnership.cylinder_id == LogisticsCylinder.id,
                    LogisticsCylinderOwnership.notes.like("seed_orphan_repair:%"),
                )
                .exists()
                |
                select(LogisticsCustomerCylinderLedger.id)
                .where(
                    LogisticsCustomerCylinderLedger.cylinder_id == LogisticsCylinder.id,
                    LogisticsCustomerCylinderLedger.source_type == "SEED_ORPHAN_REPAIR",
                )
                .exists(),
            )
        ).all()
    )

    customer_map = {customer.id: customer for customer in customers}
    now = datetime.now(UTC)

    for cylinder in orphan_cylinders:
        latest_repair_ownership = db.scalar(
            select(LogisticsCylinderOwnership.id).where(
                LogisticsCylinderOwnership.cylinder_id == cylinder.id,
                LogisticsCylinderOwnership.notes.like("seed_orphan_repair:%"),
            )
        )
        existing_repair_ledger = db.scalar(
            select(LogisticsCustomerCylinderLedger.id).where(
                LogisticsCustomerCylinderLedger.cylinder_id == cylinder.id,
                LogisticsCustomerCylinderLedger.source_type == "SEED_ORPHAN_REPAIR",
            )
        )
        if latest_repair_ownership is not None or existing_repair_ledger is not None:
            stats["skipped_repaired"] += 1
            continue

        customer_id = _repair_seed_customer_for_session(db, session_id=cylinder.session_id)
        strategy = "session"
        if customer_id is None:
            customer_id = _repair_seed_customer_for_contract(
                db,
                product_id=cylinder.product_id,
                condition=cylinder.condition,
            )
            strategy = "contract"
        if customer_id is None:
            if not fallback_allowed:
                stats["not_repairable"] += 1
                continue
            fallback_customer = _pick_seed_fallback_customer(cylinder.id, customers)
            customer_id = fallback_customer.id
            strategy = "fallback"

        customer = customer_map.get(customer_id)
        if customer is None:
            stats["unresolved"] += 1
            continue

        db.add(
            LogisticsCylinderOwnership(
                id=new_id(),
                cylinder_id=cylinder.id,
                customer_id=customer.id,
                customer_name=customer.legal_name,
                condition=cylinder.condition,
                notes=f"seed_orphan_repair:{strategy}",
                created_by=user_id,
            )
        )
        stats["ownerships_created"] += 1

        db.add(
            LogisticsCustomerCylinderLedger(
                id=new_id(),
                tenant_id=tenant_id,
                customer_id=customer.id,
                source_type="SEED_ORPHAN_REPAIR",
                source_id=cylinder.id,
                event_type="IN_TO_CUSTOMER",
                product_id=cylinder.product_id,
                product_name=db.scalar(select(Product.name).where(Product.id == cylinder.product_id)),
                condition=cylinder.condition,
                quantity=1,
                cylinder_id=cylinder.id,
                trace_mode="SERIALIZED",
                occurred_at=now,
                created_by=user_id,
                notes=f"seed_orphan_repair:{strategy}",
            )
        )
        stats["ledgers_created"] += 1

        has_state_log = db.scalar(
            select(LogisticsCylinderStateLog.id).where(
                LogisticsCylinderStateLog.cylinder_id == cylinder.id
            )
        )
        if has_state_log is None:
            db.add(
                LogisticsCylinderStateLog(
                    tenant_id=tenant_id,
                    cylinder_id=cylinder.id,
                    from_state=None,
                    to_state=cylinder.current_state,
                    changed_by=user_id,
                    origin="SEED_ORPHAN_REPAIR",
                    notes=f"seed_orphan_repair:{strategy}",
                )
            )
            stats["state_logs_created"] += 1

        if cylinder.session_id is not None:
            cylinder.session_id = None
            stats["session_links_cleared"] += 1
        cylinder.location = customer.legal_name
        db.add(cylinder)

        if strategy == "session":
            stats["resolved_by_session"] += 1
        elif strategy == "contract":
            stats["resolved_by_contract"] += 1
        else:
            stats["resolved_by_fallback"] += 1

    db.commit()
    return stats


# ── Stock balances ────────────────────────────────────────────────────

def seed_stock(db: Session, tenant_id: str, user_id: str,
               products: list, warehouses: list,
               sessions: list | None = None) -> None:
    """Create stock balances for all products at all fixed warehouses only."""
    del sessions  # mobile warehouse stock comes from load plans

    for i, product in enumerate(products):
        if product.is_service or product.condition_code == "SERVICIO":
            continue
        for warehouse in warehouses:
            qty = round(random.uniform(0, 500), 3)
            if product.condition_code == "GAS":
                qty = round(qty)
            if qty < 1:
                continue

            balance = StockBalance(
                id=new_id(), tenant_id=tenant_id,
                product_id=product.id, warehouse_id=warehouse.id,
                quantity=qty,
                reserved_quantity=round(random.uniform(0, qty * 0.3), 3),
                total_cost=round(product.name.startswith("Servicio") * 0 if product.is_service else qty * random.uniform(5, 50), 4),
                updated_by=user_id,
            )
            db.add(balance)

            config = StockConfig(
                id=new_id(), tenant_id=tenant_id,
                product_id=product.id, warehouse_id=warehouse.id,
                min_quantity=round(qty * 0.1, 3),
                max_quantity=round(qty * 2, 3),
                is_active=True, updated_by=user_id,
            )
            db.add(config)

            ledger = StockLedger(
                id=new_id(), tenant_id=tenant_id,
                product_id=product.id, warehouse_id=warehouse.id,
                operation="initial", quantity=qty, balance_after=qty,
                unit_cost=round(random.uniform(5, 50), 4),
                total_cost=round(qty * random.uniform(5, 50), 4),
                cost_after=round(qty * random.uniform(5, 50), 4),
                reference_type="seed", reference_id=f"seed-{product.id}-{warehouse.id}",
                notes="Carga inicial demo", created_by=user_id,
            )
            db.add(ledger)

        if i % 50 == 0:
            db.flush()

    db.commit()


# ── Warehouses ────────────────────────────────────────────────────────

def seed_warehouses(db: Session, tenant_id: str, branch_id: str) -> list:
    wh_defs = [
        ("CENTRAL", "Almacén Central", "Av. Industrial 1000"),
        ("NORTE", "Almacén Norte", "Panamericana Norte km 15"),
        ("SUR", "Almacén Sur", "Panamericana Sur km 20"),
        ("ESTE", "Almacén Este", "Carretera Central km 8"),
        ("PLANTA", "Planta de Llenado", "Zona Industrial Lote 10"),
    ]
    warehouses = []
    for code, name, addr in wh_defs:
        wh = LogisticsWarehouse(
            id=new_id(), tenant_id=tenant_id, code=code, name=name,
            branch_id=branch_id, address=addr,
            warehouse_type="FIXED", is_active=True,
        )
        db.add(wh)
        db.flush()
        warehouses.append(wh)
    db.commit()
    return warehouses


# ── Vehicles ──────────────────────────────────────────────────────────

def seed_vehicles(db: Session, tenant_id: str, warehouses: list) -> list:
    plates = [
        "ABC-123", "DEF-456", "GHI-789", "JKL-012", "MNO-345",
        "PQR-678", "STU-901", "VWX-234", "YZA-567", "BCD-890",
    ]
    vehicles = []
    for plate in plates:
        wh = pick_one(warehouses)
        v = LogisticsVehicle(
            id=new_id(), tenant_id=tenant_id,
            plate=plate, vehicle_type="CAMION",
            brand=random.choice(["Volvo", "Mercedes-Benz", "Scania", "Freightliner", "Hino"]),
            model=f"Modelo {random.randint(2018, 2025)}",
            capacity_weight=random.choice([2000, 3500, 5000, 8000, 12000]),
            capacity_volume=random.choice([10.0, 20.0, 30.0, 50.0]),
            warehouse_id=wh.id,
            status="ACTIVO",
            is_active=True,
        )
        db.add(v)
        db.flush()
        vehicles.append(v)
    db.commit()
    return vehicles


# ── Contract Types ────────────────────────────────────────────────────

CONTRACT_TYPE_DEFS: list[tuple[str, str, str, int]] = [
    ("COMODATO", "Comodato de cilindros", "MONTHS", 12),
    ("ALQUILER", "Alquiler de cilindros", "MONTHS", 6),
    ("VENTA", "Venta de cilindros", "DAYS", 1),
    ("MANTENIMIENTO", "Mantenimiento preventivo", "MONTHS", 3),
    ("SERVICIO_TECNICO", "Servicio técnico", "DAYS", 30),
]


def seed_contract_types(db: Session) -> list:
    contract_types = []
    for code, name, duration_unit, duration_value in CONTRACT_TYPE_DEFS:
        ct = db.scalar(select(LogisticsContractType).where(
            LogisticsContractType.code == code,
        ))
        if ct is None:
            ct = LogisticsContractType(
                code=code, name=name,
                duration_unit=duration_unit,
                duration_value=duration_value,
                is_active=True,
            )
            db.add(ct)
            db.flush()
        contract_types.append(ct)
    db.commit()
    return contract_types


# ── Contracts ──────────────────────────────────────────────────────────

def seed_contracts(
    db: Session,
    tenant_id: str,
    user_id: str,
    customers: list,
    products: list,
    warehouses: list,
) -> list:
    """Create cylinder contracts for ~30% of customers."""
    contracts = []
    gas_products = [p for p in products if p.condition_code == "GAS"]
    if not gas_products:
        return contracts

    contract_types = list(db.scalars(select(LogisticsContractType)).all())
    if not contract_types:
        return contracts

    today = date.today()

    for i, customer in enumerate(customers):
        if random.random() > 0.30:
            continue

        ct = pick_one(contract_types)
        product = pick_one(gas_products)
        wh = pick_one(warehouses)
        qty = random.randint(5, 50)

        status_options = ["DRAFT", "ACTIVE", "ACTIVE", "ACTIVE", "TERMINATED"]
        status = status_options[i % len(status_options)]

        start_date = today - timedelta(days=random.randint(30, 730))
        end_date = start_date + timedelta(days=random.randint(90, 365))
        if status == "TERMINATED":
            end_date = today - timedelta(days=random.randint(1, 90))

        series = f"CT-{i+1:04d}"
        contract = LogisticsCylinderContract(
            id=new_id(),
            tenant_id=tenant_id,
            warehouse_id=wh.id,
            contract_number=f"{series}-{random.randint(1,99):02d}",
            document_type_code=4,
            series=series,
            number=i + 1,
            contract_type=ct.code,
            status=status,
            customer_id=customer.id,
            start_date=start_date,
            end_date=end_date if status != "ACTIVE" else None,
            cylinder_type_id=product.id,
            cylinder_condition="GAS",
            quantity=qty,
            unit_price=round(random.uniform(5, 50), 4),
            signed_flag=status in ("ACTIVE", "TERMINATED"),
            signed_at=datetime.now(UTC) - timedelta(days=random.randint(1, 30))
            if status in ("ACTIVE", "TERMINATED") else None,
            notes=f"Contrato {ct.name} - {qty} cilindros {product.name}",
            is_active=status != "TERMINATED",
            created_by=user_id,
        )
        db.add(contract)
        contracts.append(contract)

        if i % 10 == 0:
            db.flush()

    db.commit()
    return contracts


# ── Quotes (Cotizaciones) ─────────────────────────────────────────────

def seed_quotes(
    db: Session,
    tenant_id: str,
    user_id: str,
    customers: list,
    products: list,
    vehicles: list,
) -> list[QuoteDraft]:
    """Create 15-20 quote drafts for random customers."""
    quotes: list[QuoteDraft] = []
    gas_products = [p for p in products if p.condition_code == "GAS"]
    if not gas_products or not customers:
        return quotes

    today = date.today()
    for i in range(18):
        customer = pick_one(customers)
        vehicle = pick_one(vehicles)
        delivery_date = today + timedelta(days=random.randint(1, 14))
        status = "DRAFT" if i < 12 else "CONFIRMED"

        quote = QuoteDraft(
            id=new_id(),
            tenant_id=tenant_id,
            customer_id=customer.id,
            customer_name=customer.commercial_name or customer.legal_name,
            status=status,
            delivery_date=delivery_date,
            vehicle_id=vehicle.id,
            vehicle_plate=vehicle.plate,
            conditions="Pago contra entrega. Precios incluyen IGV.",
            notes=f"Cotización demo #{i+1}",
            created_by=user_id,
            updated_by=user_id if status == "CONFIRMED" else None,
        )
        db.add(quote)
        db.flush()

        num_items = random.randint(2, 5)
        item_list: list[dict] = []
        for _ in range(num_items):
            product = pick_one(gas_products)
            qty = random.randint(1, 20)
            db.add(QuoteItem(
                id=new_id(),
                quote_draft_id=quote.id,
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
            ))
            item_list.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": qty,
            })

        quotes.append(quote)

    db.commit()
    return quotes


# ── Planning Reservations ─────────────────────────────────────────────

def seed_planning_reservations(
    db: Session,
    tenant_id: str,
    user_id: str,
    vehicles: list,
    warehouses: list,
    quotes: list,
) -> list[LogisticsPlanningReservation]:
    """Create planning reservations, some linked to quotes."""
    reservations: list[LogisticsPlanningReservation] = []
    now = datetime.now(UTC)

    statuses = ["PLANNED", "PLANNED", "PLANNED", "PLANNED",
                "ACTIVATED", "ACTIVATED", "CANCELLED", "COMPLETED"]

    for i, vehicle in enumerate(vehicles):
        wh = pick_one(warehouses)
        start = now + timedelta(hours=random.randint(1, 72))
        end = start + timedelta(hours=random.randint(2, 8))
        status = statuses[i % len(statuses)]
        quote_id = None
        load_summary: dict = {"items": []}

        if quotes and random.random() < 0.4:
            quote = pick_one(quotes)
            quote_id = quote.id
            items = list(db.scalars(
                select(QuoteItem).where(QuoteItem.quote_draft_id == quote.id)
            ).all())
            load_summary = {
                "items": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                    }
                    for item in items
                ],
                "quote_id": quote_id,
            }

        reservation = LogisticsPlanningReservation(
            id=new_id(),
            tenant_id=tenant_id,
            vehicle_id=vehicle.id,
            origin_warehouse_id=wh.id,
            planned_start_at=start,
            planned_end_at=end,
            expected_load_summary=load_summary,
            expected_weight_total=None,
            status=status,
            quote_id=quote_id,
            driver_id=user_id,
            notes=f"Reserva planificación demo #{i+1}",
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(reservation)
        reservations.append(reservation)

        if i % 3 == 0:
            db.flush()

    db.commit()
    return reservations


# ── Sessions ──────────────────────────────────────────────────────────

def seed_sessions(
    db: Session,
    tenant_id: str,
    branch_id: str,
    user_id: str,
    vehicles: list,
    warehouses: list,
    products: list,
) -> list:
    """Create sessions at various stages with realistic load plans."""
    sessions: list[LogisticsVehicleSession] = []
    now = datetime.now(UTC)
    gas_products = [p for p in products if p.condition_code == "GAS"]

    for i, vehicle in enumerate(vehicles):
        wh = pick_one(warehouses)
        mobile_id = new_id()

        mobile_wh = LogisticsWarehouse(
            id=mobile_id, tenant_id=tenant_id,
            code=f"MOB-{vehicle.plate}", name=f"Móvil {vehicle.plate}",
            branch_id=branch_id, address=None,
            warehouse_type="MOBILE", is_active=True,
        )
        db.add(mobile_wh)
        db.flush()

        route = LogisticsRoute(
            id=new_id(), tenant_id=tenant_id,
            vehicle_id=vehicle.id,
            driver_id=user_id,
            route_date=now.date(),
            status="EN_RUTA",
            created_by=user_id,
        )
        db.add(route)
        db.flush()

        status_order = [
            "CLOSED", "CLOSED",
            "AWAITING_RECONCILIATION",
            "OUTBOUND", "OUTBOUND", "OUTBOUND",
            "LOADING", "LOADING",
            "DRAFT",
        ]
        session_status = status_order[i % len(status_order)]

        departed_at = None
        if session_status in ("OUTBOUND", "RETURNING", "AWAITING_RECONCILIATION", "CLOSED"):
            departed_at = now - timedelta(hours=random.randint(2, 48))

        returned_at = None
        if session_status in ("AWAITING_RECONCILIATION", "CLOSED"):
            returned_at = (departed_at or now) + timedelta(hours=random.randint(4, 12))

        loaded_weight = round(random.uniform(500, 8000), 2) if session_status != "DRAFT" else None

        session = LogisticsVehicleSession(
            id=new_id(), tenant_id=tenant_id,
            branch_id=branch_id,
            vehicle_id=vehicle.id,
            driver_id=user_id,
            origin_warehouse_id=wh.id,
            mobile_warehouse_id=mobile_wh.id,
            route_id=route.id,
            status=session_status,
            departed_at=departed_at,
            returned_at=returned_at,
            loaded_weight_kg=loaded_weight,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(session)
        db.flush()
        sessions.append(session)

        if session_status in ("LOADING", "OUTBOUND", "RETURNING", "AWAITING_RECONCILIATION"):
            load_plan = LogisticsLoadPlan(
                id=new_id(), tenant_id=tenant_id,
                session_id=session.id,
                status="CONFIRMED",
                created_by=user_id,
            )
            db.add(load_plan)
            db.flush()
            num_items = random.randint(2, 4)
            for _ in range(num_items):
                product = pick_one(gas_products)
                planned_qty = random.randint(3, 15)
                db.add(LogisticsLoadPlanItem(
                    id=new_id(),
                    load_plan_id=load_plan.id,
                    product_id=product.id,
                    product_name=product.name,
                    planned_quantity=planned_qty,
                    source_warehouse_id=wh.id,
                ))

    db.commit()
    return sessions


# ── Clear existing data ──────────────────────────────────────────────

def clear_demo_data(db: Session) -> None:
    """Delete all demo data using TRUNCATE CASCADE for reliability."""
    table_prefixes = ("stk_", "lg_", "ventas_", "prod_", "crm_")
    # Keep static seed tables (populated by migrations)
    keep_tables = {"prod_status", "prod_conditions", "crm_document_types",
                   "crm_payment_terms", "crm_geography", "lg_cylinder_states", "crm_geography", "lg_cylinder_states",
                   "lg_state_transitions", "lg_movement_types", "lg_agenda_task_types",
                   "lg_service_types"}
    from sqlalchemy import inspect
    all_tables = inspect(db.connection()).get_table_names()
    for table in all_tables:
        if any(table.startswith(p) for p in table_prefixes):
            if table in keep_tables:
                continue
            try:
                db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass
    db.commit()


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    settings = Settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(settings)

    with session_factory() as db:
        registry = PluginManifestRegistry(settings.plugins_dir)
        registry.discover()
        sync_plugin_registry_state(db, registry=registry)

        print("Seeding tenant, user, roles...")
        plugins_list = [
            r for r in registry._plugins  # noqa: SLF001
        ]
        from apps.api.app.kernel.plugins.runtime import LoadedPlugin
        loaded = [
            LoadedPlugin(
                plugin_id=p.plugin_id, root=p.root,
                status="valid" if p.is_valid else "failed",
                manifest=p.manifest, lifecycle=["discovered", "validated", "loaded"],
            )
            for p in plugins_list
        ]
        seeded = seed_demo_data(db, settings, loaded)
        tenant_id = seeded["tenant_id"]
        user_id = seeded["user_id"]
        branch_id = seeded["branch_id"]

        print("Clearing existing demo data...")
        clear_demo_data(db)

        print("Creating catalogs...")
        catalogs = seed_catalogs(db, tenant_id)

        print("Creating 600 products...")
        products = seed_products(db, tenant_id, user_id, catalogs)

        print("Creating warehouses...")
        warehouses = seed_warehouses(db, tenant_id, branch_id)

        print("Creating vehicles...")
        vehicles = seed_vehicles(db, tenant_id, warehouses)

        print("Creating sessions (2 closed, 1 reconciling, 3 outbound, 2 loading, 1 draft)...")
        sessions = seed_sessions(db, tenant_id, branch_id, user_id, vehicles, warehouses, products)

        print("Creating 100 customers...")
        customers = seed_customers(db, tenant_id, user_id)

        print("Creating contract types and contracts for ~30 customers...")
        seed_contract_types(db)
        seed_contracts(db, tenant_id, user_id, customers, products, warehouses)

        print("Creating 18 quote drafts (cotizaciones)...")
        quotes = seed_quotes(db, tenant_id, user_id, customers, products, vehicles)

        print("Creating 10 planning reservations...")
        seed_planning_reservations(db, tenant_id, user_id, vehicles, warehouses, quotes)

        print("Creating 3000 cylinders...")
        seed_cylinders(db, tenant_id, user_id, products, warehouses, customers, sessions)

        print("Assigning serials to load plans...")
        seed_load_serial_assignments(db, tenant_id, user_id, sessions)

        print("Repairing orphan customer-possession cylinders...")
        repair_stats = repair_seed_customer_possession_orphans(
            db,
            tenant_id,
            user_id,
            customers,
            env=settings.env,
            allow_fallback=settings.allow_seed_orphan_repair_fallback,
        )

        print("Creating stock balances...")
        seed_stock(db, tenant_id, user_id, products, warehouses, sessions)

        total_products = db.scalar(select(text("count(*) from prod_products")))
        total_cylinders = db.scalar(select(text("count(*) from lg_cylinders")))
        total_customers = db.scalar(select(text("count(*) from crm_customers")))
        total_balances = db.scalar(select(text("count(*) from stk_balance")))
        total_contracts = db.scalar(select(text("count(*) from lg_cylinder_contracts")))
        total_quotes = db.scalar(select(text("count(*) from ventas_quote_drafts")))
        total_reservations = db.scalar(
            select(text("count(*) from lg_planning_reservations"))
        )

    engine.dispose()

    print("\n✅ Seed completo:")
    print(f"   Productos:    {total_products}")
    print(f"   Cilindros:    {total_cylinders}")
    print(f"   Clientes:     {total_customers}")
    print(f"   Contratos:    {total_contracts}")
    print(f"   Cotizaciones: {total_quotes}")
    print(f"   Reservas:     {total_reservations}")
    print(f"   Balances:     {total_balances}")
    print(
        "   Repair orphans: "
        f"session={repair_stats['resolved_by_session']} · "
        f"contract={repair_stats['resolved_by_contract']} · "
        f"fallback={repair_stats['resolved_by_fallback']} · "
        f"skipped={repair_stats['skipped_repaired']} · "
        f"not_repairable={repair_stats['not_repairable']} · "
        f"unresolved={repair_stats['unresolved']}"
    )
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
