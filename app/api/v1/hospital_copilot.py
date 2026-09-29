from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.api.v1.dashboard_auth import (
    dashboard_user,
)
from app.core.database import (
    get_db,
)
from app.models.hospital import (
    Hospital,
)
from app.schemas.hospital_copilot import (
    HospitalCopilotProposal,
    HospitalCopilotProposalConfirmation,
    HospitalCopilotProposalCreate,
    HospitalCopilotRequest,
    HospitalCopilotResponse,
)
from app.services.hospital_copilot import (
    HospitalCopilotService,
)
from app.services.hospital_copilot_proposals import (
    CopilotProposalError,
    HospitalCopilotProposalService,
)
from app.services.tenant_authorization import (
    HospitalNotFound,
    TenantAccessDenied,
    get_active_hospital,
    require_hospital_access,
    require_hospital_admin,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-copilot"],
)


async def _hospital(
    session: AsyncSession,
    *,
    hospital_slug: str,
    current_user,
    admin: bool = False,
) -> Hospital:
    hospital = await get_active_hospital(
        session,
        hospital_slug=hospital_slug,
    )

    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    try:
        if admin:
            await require_hospital_admin(
                session,
                user_id=current_user.id,
                hospital_id=hospital.id,
            )

        else:
            await require_hospital_access(
                session,
                user_id=current_user.id,
                hospital_id=hospital.id,
            )

    except HospitalNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        ) from exc

    except TenantAccessDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        ) from exc

    return hospital


def _proposal_service(
    session: AsyncSession,
    hospital: Hospital,
    current_user,
):
    return HospitalCopilotProposalService(
        session,
        hospital_id=hospital.id,
        user_id=current_user.id,
        hospital_slug=hospital.slug,
        current_user=current_user,
    )


@router.post(
    "/{hospital_slug}/copilot/query",
    response_model=HospitalCopilotResponse,
)
async def hospital_copilot_query(
    hospital_slug: str,
    payload: HospitalCopilotRequest,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital(
        session,
        hospital_slug=hospital_slug,
        current_user=current_user,
    )

    service = HospitalCopilotService(
        session,
        hospital_id=hospital.id,
        hospital_slug=hospital.slug,
    )

    intent, mode = await service.interpret(
        payload.message
    )

    tools = await service.run(
        intent
    )

    answer = service.render(
        intent,
        tools,
    )

    proposals = _proposal_service(
        session,
        hospital,
        current_user,
    )

    await proposals.audit_query(
        message=payload.message,
        intent=intent.value,
        mode=mode,
    )

    return HospitalCopilotResponse(
        intent=intent,
        answer=answer,
        mode=mode,
        tools=tools,
        proposal_required=(
            intent.value
            in {
                "propose_capacity",
                "propose_closure",
            }
        ),
    )


@router.post(
    "/{hospital_slug}/copilot/proposals",
    response_model=HospitalCopilotProposal,
)
async def create_copilot_proposal(
    hospital_slug: str,
    payload: HospitalCopilotProposalCreate,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital(
        session,
        hospital_slug=hospital_slug,
        current_user=current_user,
        admin=True,
    )

    service = _proposal_service(
        session,
        hospital,
        current_user,
    )

    try:
        return await service.create(
            payload.action_type,
            payload.payload,
        )

    except (
        CopilotProposalError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "/{hospital_slug}/copilot/proposals/{proposal_id}",
    response_model=HospitalCopilotProposal,
)
async def get_copilot_proposal(
    hospital_slug: str,
    proposal_id: str,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital(
        session,
        hospital_slug=hospital_slug,
        current_user=current_user,
    )

    service = _proposal_service(
        session,
        hospital,
        current_user,
    )

    try:
        return await service.get(
            proposal_id
        )

    except CopilotProposalError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        ) from exc


@router.post(
    "/{hospital_slug}/copilot/proposals/{proposal_id}/confirm",
    response_model=HospitalCopilotProposal,
)
async def confirm_copilot_proposal(
    hospital_slug: str,
    proposal_id: str,
    payload:
        HospitalCopilotProposalConfirmation,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital(
        session,
        hospital_slug=hospital_slug,
        current_user=current_user,
        admin=True,
    )

    service = _proposal_service(
        session,
        hospital,
        current_user,
    )

    try:
        return await service.confirm(
            proposal_id,
            confirm=payload.confirm,
        )

    except CopilotProposalError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            ),
        ) from exc


@router.post(
    "/{hospital_slug}/copilot/proposals/{proposal_id}/execute",
    response_model=HospitalCopilotProposal,
)
async def execute_copilot_proposal(
    hospital_slug: str,
    proposal_id: str,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital(
        session,
        hospital_slug=hospital_slug,
        current_user=current_user,
        admin=True,
    )

    service = _proposal_service(
        session,
        hospital,
        current_user,
    )

    try:
        return await service.execute(
            proposal_id
        )

    except CopilotProposalError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            ),
        ) from exc
