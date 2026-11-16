# backend/schemas/__init__.py
from backend.schemas.machine import (
    MachineBaseSchema,
    MachineDetailSchema,
    MachineHistoryPoint,
    MachineHistoryResponse,
    PredictionSummarySchema,
    SensorReadingSchema,
)
from backend.schemas.simulation import (
    SimulationControlResponse,
    SimulationJumpRequest,
    SimulationSpeedRequest,
    SimulationStatusSchema,
    SimulationStepRequest,
)
from backend.schemas.alert import IncidentSchema, ResolveAlertRequest
from backend.schemas.business import (
    BusinessImpactSchema,
    FleetSummarySchema,
    HealingDecisionSchema,
    HealingTriggerRequest,
)
from backend.schemas.whatif import (
    MachineScenarioParamSchema,
    WhatIfComparisonResponse,
    WhatIfHistoryItemSchema,
    WhatIfRunRequest,
    WhatIfTemplateSchema,
)

__all__ = [
    "MachineBaseSchema",
    "MachineDetailSchema",
    "MachineHistoryPoint",
    "MachineHistoryResponse",
    "PredictionSummarySchema",
    "SensorReadingSchema",
    "SimulationControlResponse",
    "SimulationJumpRequest",
    "SimulationSpeedRequest",
    "SimulationStatusSchema",
    "SimulationStepRequest",
    "IncidentSchema",
    "ResolveAlertRequest",
    "BusinessImpactSchema",
    "FleetSummarySchema",
    "HealingDecisionSchema",
    "HealingTriggerRequest",
    "MachineScenarioParamSchema",
    "WhatIfComparisonResponse",
    "WhatIfHistoryItemSchema",
    "WhatIfRunRequest",
    "WhatIfTemplateSchema",
]
