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
)
from .customer_possession import LogisticsCustomerCylinderLedger
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
from .load_plans import LogisticsLoadPlan, LogisticsLoadPlanItem
from .load_serial_assignments import LogisticsLoadSerialAssignment
from .movements import LogisticsMovement, LogisticsMovementItem, LogisticsMovementStatusHistory
from .operations import (
    LogisticsLoad,
    LogisticsOrder,
    LogisticsOrderItem,
    LogisticsRoute,
    LogisticsRouteStop,
)
from .planning import (
    LogisticsPlanningReservation,
    LogisticsPlanPreload,
    LogisticsPlanPreloadItem,
    LogisticsReceptionIncident,
)
from .reconciliation import LogisticsInventoryDiscrepancy, LogisticsSessionReconciliation
from .resources import (
    LogisticsDeliveryPoint,
    LogisticsVehicle,
    LogisticsVehicleDeliveryPoint,
    LogisticsWarehouse,
    LogisticsZone,
)
from .route_incidents import LogisticsRouteIncident
from .route_operations import LogisticsRouteOperation, LogisticsRouteOperationItem
from .route_stop_results import LogisticsRouteStopResult
from .session_operations import LogisticsOperation, LogisticsOperationItem
from .session_waybills import LogisticsSessionWaybillVersion
from .sessions import LogisticsVehicleSession
