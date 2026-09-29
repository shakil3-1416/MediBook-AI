from app.api.v1 import platform_control_v2
from app.api.v1 import hospital_copilot
from app.api.v1 import hospital_staff_admin
from app.api.v1 import hospital_public
from app.api.v1 import workspaces
from app.api.v1 import conversations
from app.api.v1 import auth
from fastapi import APIRouter

from app.api.v1 import (
    appointments,
    availability,
    chat,
    doctors,
    llm,
    llm_diagnostics,
)


api_router = APIRouter()


api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"],
)

api_router.include_router(
    doctors.router,
    prefix="/doctors",
    tags=["doctors"],
)

api_router.include_router(
    availability.router,
    prefix="/availability",
    tags=["availability"],
)

api_router.include_router(
    appointments.router,
    prefix="/appointments",
    tags=["appointments"],
)


api_router.include_router(
    llm.router,
    prefix="/llm",
    tags=["llm"],
)


api_router.include_router(
    llm_diagnostics.router,
    prefix="/llm-diagnostics",
    tags=["llm-diagnostics"],
)


api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)


api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["conversations"],
)
api_router.include_router(workspaces.router)

# Hospital-scoped public widget API
api_router.include_router(hospital_public.router)

from app.api.v1 import hospital_doctor_registry
api_router.include_router(hospital_doctor_registry.router)

from app.api.v1 import hospital_schedules
api_router.include_router(hospital_schedules.router)


from app.api.v1 import hospital_integrations
api_router.include_router(hospital_integrations.router)

from app.api.v1 import hospital_admin_ops
api_router.include_router(hospital_admin_ops.router)

from app.api.v1 import platform_control
api_router.include_router(platform_control.router)

api_router.include_router(hospital_staff_admin.router)

api_router.include_router(hospital_copilot.router)

api_router.include_router(platform_control_v2.router)
