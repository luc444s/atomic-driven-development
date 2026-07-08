# Auto-generado por split_logistics_models.py
# Re-exporta todas las clases para retrocompatibilidad.
# ruff: noqa: F401
from __future__ import annotations

from .adr import LogisticsAdrIncompatibility, LogisticsAdrProductConfig
from .agenda import LogisticsAgendaTask, LogisticsRouteWeekday
from .catalog import (
    LogisticsAgendaTaskType,
    LogisticsMovementType,
    LogisticsServiceType,
)
from .contracts import (
    LogisticsContractType,
    LogisticsCylinderContract,
    LogisticsCylinderContractHistory,
    LogisticsCylinderContractItem,
)
from .cylinder import (
    LogisticsCylinder,
    LogisticsCylinderLabelHistory,
    LogisticsCylinderOwnership,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
    LogisticsCylinderState,
    LogisticsCylinderStateLog,
    LogisticsCylinderWarranty,
    LogisticsHydrostaticTest,
    LogisticsScanLog,
    LogisticsStateTransition,
)
from .equipment import (
    LogisticsDriverParameter,
    LogisticsEquipment,
    LogisticsMovementEquipment,
    LogisticsVehicleRouteRestriction,
)
from .movements import LogisticsMovement, LogisticsMovementItem, LogisticsMovementStatusHistory
from .operations import (
    LogisticsLoad,
    LogisticsOrder,
    LogisticsOrderItem,
    LogisticsRoute,
    LogisticsRouteStop,
)
from .planning import LogisticsPlanPreload, LogisticsPlanPreloadItem, LogisticsReceptionIncident
from .resources import (
    LogisticsDeliveryPoint,
    LogisticsVehicle,
    LogisticsVehicleDeliveryPoint,
    LogisticsWarehouse,
    LogisticsZone,
)
