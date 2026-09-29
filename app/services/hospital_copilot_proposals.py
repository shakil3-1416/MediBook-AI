from __future__ import annotations

from datetime import (
    date,
    datetime,
    timezone,
)
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.schemas.hospital_copilot import (
    CapacityProposalPayload,
    ClosureProposalPayload,
    HospitalCopilotActionType,
    HospitalCopilotProposal,
)

from app.services.hospital_copilot_schedule_executor import (
    CopilotScheduleExecutionError,
    HospitalCopilotScheduleExecutor,
)


class CopilotProposalError(
    ValueError
):
    pass


class HospitalCopilotProposalService:
    """
    Durable proposal lifecycle.

    This service persists proposals and confirmations.

    It intentionally does NOT bypass the existing
    Schedule Engine. execution_supported remains false
    until an existing deterministic Schedule Engine
    apply contract is positively identified and wired.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        hospital_id,
        user_id,
        hospital_slug: str | None = None,
        current_user=None,
    ):
        self.session = session
        self.hospital_id = str(
            hospital_id
        )
        self.user_id = str(
            user_id
        )
        self.hospital_slug = (
            hospital_slug
        )
        self.current_user = (
            current_user
        )


    async def _event(
        self,
        event_type: str,
        detail: dict[
            str,
            Any,
        ],
        *,
        proposal_id:
            str | None = None,
    ) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO hospital_copilot_events
                    (
                        id,
                        hospital_id,
                        user_id,
                        event_type,
                        proposal_id,
                        detail,
                        created_at
                    )
                VALUES
                    (
                        :id,
                        :hospital_id,
                        :user_id,
                        :event_type,
                        :proposal_id,
                        CAST(:detail AS json),
                        :created_at
                    )
                """
            ),
            {
                "id":
                    str(
                        uuid.uuid4()
                    ),

                "hospital_id":
                    self.hospital_id,

                "user_id":
                    self.user_id,

                "event_type":
                    event_type,

                "proposal_id":
                    proposal_id,

                "detail":
                    __import__(
                        "json"
                    ).dumps(
                        detail
                    ),

                "created_at":
                    datetime.now(
                        timezone.utc
                    ),
            },
        )


    async def audit_query(
        self,
        *,
        message: str,
        intent: str,
        mode: str,
    ) -> None:
        await self._event(
            "copilot.query",
            {
                "message":
                    message,
                "intent":
                    intent,
                "mode":
                    mode,
            },
        )

        await self.session.commit()


    async def _capacity_impact(
        self,
        payload:
            CapacityProposalPayload,
    ) -> dict[
        str,
        Any,
    ]:
        row = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        r.id,
                        r.capacity,
                        r.weekday,
                        r.start_time,
                        r.end_time,
                        r.is_active,
                        hd.id AS hospital_doctor_id,
                        hd.doctor_id
                    FROM doctor_schedule_rules r
                    JOIN hospital_doctors hd
                      ON hd.id = r.hospital_doctor_id
                    WHERE r.id = :rule_id
                      AND hd.hospital_id = :hospital_id
                    LIMIT 1
                    """
                ),
                {
                    "rule_id":
                        payload.schedule_rule_id,

                    "hospital_id":
                        self.hospital_id,
                },
            )
        ).mappings().first()

        if row is None:
            raise CopilotProposalError(
                "Schedule rule was not found "
                "inside this hospital."
            )

        current_capacity = int(
            row[
                "capacity"
            ]
        )

        return {
            "schedule_rule_id":
                str(
                    row[
                        "id"
                    ]
                ),

            "hospital_doctor_id":
                str(
                    row[
                        "hospital_doctor_id"
                    ]
                ),

            "doctor_id":
                str(
                    row[
                        "doctor_id"
                    ]
                ),

            "weekday":
                row[
                    "weekday"
                ],

            "current_capacity":
                current_capacity,

            "proposed_capacity":
                payload.new_capacity,

            "capacity_delta":
                (
                    payload.new_capacity
                    - current_capacity
                ),

            "rule_active":
                bool(
                    row[
                        "is_active"
                    ]
                ),

            "execution_note":
                (
                    "Proposal is durable, but execution "
                    "must use the existing Schedule Engine "
                    "apply contract."
                ),
        }


    async def _closure_impact(
        self,
        payload:
            ClosureProposalPayload,
    ) -> dict[
        str,
        Any,
    ]:
        doctor = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        hd.id,
                        hd.doctor_id,
                        hd.is_active
                    FROM hospital_doctors hd
                    WHERE hd.id = :hospital_doctor_id
                      AND hd.hospital_id = :hospital_id
                    LIMIT 1
                    """
                ),
                {
                    "hospital_doctor_id":
                        payload.hospital_doctor_id,

                    "hospital_id":
                        self.hospital_id,
                },
            )
        ).mappings().first()

        if doctor is None:
            raise CopilotProposalError(
                "Hospital doctor mapping was not found "
                "inside this hospital."
            )

        try:
            closure_date = (
                date.fromisoformat(
                    payload.date
                )
            )

        except ValueError as exc:
            raise CopilotProposalError(
                "Closure date must use YYYY-MM-DD."
            ) from exc


        appointments = (
            await self.session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM appointments
                    WHERE hospital_id = :hospital_id
                      AND doctor_id = :doctor_id
                      AND status NOT IN
                          (
                              'cancelled',
                              'canceled'
                          )
                    """
                ),
                {
                    "hospital_id":
                        self.hospital_id,

                    "doctor_id":
                        str(
                            doctor[
                                "doctor_id"
                            ]
                        ),
                },
            )
        ).scalar()


        return {
            "hospital_doctor_id":
                str(
                    doctor[
                        "id"
                    ]
                ),

            "doctor_id":
                str(
                    doctor[
                        "doctor_id"
                    ]
                ),

            "date":
                closure_date.isoformat(),

            "reason":
                payload.reason,

            "doctor_active":
                bool(
                    doctor[
                        "is_active"
                    ]
                ),

            "hospital_doctor_appointment_count":
                int(
                    appointments or 0
                ),

            "execution_note":
                (
                    "This is an impact preview only. "
                    "The existing Schedule Engine must "
                    "perform the closure mutation."
                ),
        }


    async def create(
        self,
        action_type:
            HospitalCopilotActionType,
        payload:
            dict[
                str,
                Any,
            ],
    ) -> HospitalCopilotProposal:

        if (
            action_type
            ==
            HospitalCopilotActionType
            .SCHEDULE_CAPACITY_CHANGE
        ):
            typed = (
                CapacityProposalPayload
                .model_validate(
                    payload
                )
            )

            impact = (
                await self
                ._capacity_impact(
                    typed
                )
            )

            normalized_payload = (
                typed.model_dump()
            )

        elif (
            action_type
            ==
            HospitalCopilotActionType
            .SCHEDULE_CLOSURE
        ):
            typed = (
                ClosureProposalPayload
                .model_validate(
                    payload
                )
            )

            impact = (
                await self
                ._closure_impact(
                    typed
                )
            )

            normalized_payload = (
                typed.model_dump()
            )

        else:
            raise CopilotProposalError(
                "Unsupported proposal action."
            )


        proposal_id = str(
            uuid.uuid4()
        )

        now = datetime.now(
            timezone.utc
        )


        await self.session.execute(
            text(
                """
                INSERT INTO hospital_copilot_proposals
                    (
                        id,
                        hospital_id,
                        created_by_user_id,
                        action_type,
                        payload,
                        impact,
                        status,
                        execution_supported,
                        created_at
                    )
                VALUES
                    (
                        :id,
                        :hospital_id,
                        :user_id,
                        :action_type,
                        CAST(:payload AS json),
                        CAST(:impact AS json),
                        'pending',
                        TRUE,
                        :created_at
                    )
                """
            ),
            {
                "id":
                    proposal_id,

                "hospital_id":
                    self.hospital_id,

                "user_id":
                    self.user_id,

                "action_type":
                    action_type.value,

                "payload":
                    __import__(
                        "json"
                    ).dumps(
                        normalized_payload
                    ),

                "impact":
                    __import__(
                        "json"
                    ).dumps(
                        impact
                    ),

                "created_at":
                    now,
            },
        )


        await self._event(
            "copilot.proposal.created",
            {
                "action_type":
                    action_type.value,

                "payload":
                    normalized_payload,

                "impact":
                    impact,
            },
            proposal_id=
                proposal_id,
        )


        await self.session.commit()


        return HospitalCopilotProposal(
            id=proposal_id,
            action_type=action_type,
            payload=
                normalized_payload,
            impact=impact,
            status="pending",
            execution_supported=True,
        )


    async def get(
        self,
        proposal_id: str,
    ) -> HospitalCopilotProposal:
        row = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        id,
                        action_type,
                        payload,
                        impact,
                        status,
                        execution_supported,
                        execution_result
                    FROM hospital_copilot_proposals
                    WHERE id = :id
                      AND hospital_id = :hospital_id
                    LIMIT 1
                    """
                ),
                {
                    "id":
                        proposal_id,

                    "hospital_id":
                        self.hospital_id,
                },
            )
        ).mappings().first()


        if row is None:
            raise CopilotProposalError(
                "Proposal was not found."
            )


        return HospitalCopilotProposal(
            id=str(
                row[
                    "id"
                ]
            ),

            action_type=
                HospitalCopilotActionType(
                    row[
                        "action_type"
                    ]
                ),

            payload=
                dict(
                    row[
                        "payload"
                    ]
                    or {}
                ),

            impact=
                dict(
                    row[
                        "impact"
                    ]
                    or {}
                ),

            status=
                str(
                    row[
                        "status"
                    ]
                ),

            execution_supported=
                bool(
                    row[
                        "execution_supported"
                    ]
                ),

            execution_result=
                (
                    dict(
                        row[
                            "execution_result"
                        ]
                    )
                    if row[
                        "execution_result"
                    ]
                    else None
                ),
        )


    async def confirm(
        self,
        proposal_id: str,
        *,
        confirm: bool,
    ) -> HospitalCopilotProposal:
        proposal = await self.get(
            proposal_id
        )


        if (
            proposal.status
            != "pending"
        ):
            raise CopilotProposalError(
                "Only pending proposals can "
                "be confirmed or cancelled."
            )


        now = datetime.now(
            timezone.utc
        )


        if not confirm:
            await self.session.execute(
                text(
                    """
                    UPDATE hospital_copilot_proposals
                    SET status = 'cancelled',
                        cancelled_at = :now
                    WHERE id = :id
                      AND hospital_id = :hospital_id
                    """
                ),
                {
                    "id":
                        proposal_id,

                    "hospital_id":
                        self.hospital_id,

                    "now":
                        now,
                },
            )

            await self._event(
                "copilot.proposal.cancelled",
                {},
                proposal_id=
                    proposal_id,
            )

            await self.session.commit()

            return await self.get(
                proposal_id
            )


        await self.session.execute(
            text(
                """
                UPDATE hospital_copilot_proposals
                SET status = 'confirmed',
                    confirmed_at = :now
                WHERE id = :id
                  AND hospital_id = :hospital_id
                """
            ),
            {
                "id":
                    proposal_id,

                "hospital_id":
                    self.hospital_id,

                "now":
                    now,
            },
        )


        await self._event(
            "copilot.proposal.confirmed",
            {
                "execution_supported":
                    proposal.execution_supported,
            },
            proposal_id=
                proposal_id,
        )


        await self.session.commit()


        confirmed = await self.get(
            proposal_id
        )


        # Fail closed:
        # confirmation does not mutate the schedule until the
        # existing Schedule Engine apply contract is wired.
        return confirmed


    async def execute(
        self,
        proposal_id: str,
    ) -> HospitalCopilotProposal:
        proposal = await self.get(
            proposal_id
        )

        if (
            proposal.status
            != "confirmed"
        ):
            raise CopilotProposalError(
                "Only confirmed proposals can be executed."
            )

        if (
            not proposal.execution_supported
        ):
            raise CopilotProposalError(
                "Execution is not supported for this proposal."
            )

        if (
            not self.hospital_slug
            or self.current_user
            is None
        ):
            raise CopilotProposalError(
                "Execution context is incomplete."
            )

        executor = (
            HospitalCopilotScheduleExecutor(
                self.session,
                hospital_id=
                    self.hospital_id,
                hospital_slug=
                    self.hospital_slug,
                current_user=
                    self.current_user,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        try:
            if (
                proposal.action_type
                ==
                HospitalCopilotActionType
                .SCHEDULE_CAPACITY_CHANGE
            ):
                result = (
                    await executor.execute_capacity_change(
                        proposal.payload,
                        proposal.impact,
                    )
                )

            elif (
                proposal.action_type
                ==
                HospitalCopilotActionType
                .SCHEDULE_CLOSURE
            ):
                result = (
                    await executor.execute_closure(
                        proposal.payload,
                        proposal.impact,
                    )
                )

            else:
                raise CopilotProposalError(
                    "Unsupported proposal action."
                )

            await self.session.execute(
                text(
                    """
                    UPDATE hospital_copilot_proposals
                    SET status = 'executed',
                        executed_at = :now,
                        execution_result = CAST(
                            :execution_result
                            AS json
                        )
                    WHERE id = :id
                      AND hospital_id = :hospital_id
                      AND status = 'confirmed'
                    """
                ),
                {
                    "id":
                        proposal_id,

                    "hospital_id":
                        self.hospital_id,

                    "now":
                        now,

                    "execution_result":
                        __import__(
                            "json"
                        ).dumps(
                            result
                        ),
                },
            )

            await self._event(
                "copilot.proposal.executed",
                {
                    "action_type":
                        proposal.action_type.value,

                    "result":
                        result,
                },
                proposal_id=
                    proposal_id,
            )

            await self.session.commit()

            return await self.get(
                proposal_id
            )

        except Exception as exc:
            await self.session.rollback()

            failure = {
                "error_type":
                    type(
                        exc
                    ).__name__,

                "message":
                    str(
                        exc
                    ),
            }

            await self.session.execute(
                text(
                    """
                    UPDATE hospital_copilot_proposals
                    SET status = 'failed',
                        executed_at = :now,
                        execution_result = CAST(
                            :execution_result
                            AS json
                        )
                    WHERE id = :id
                      AND hospital_id = :hospital_id
                      AND status = 'confirmed'
                    """
                ),
                {
                    "id":
                        proposal_id,

                    "hospital_id":
                        self.hospital_id,

                    "now":
                        now,

                    "execution_result":
                        __import__(
                            "json"
                        ).dumps(
                            failure
                        ),
                },
            )

            await self._event(
                "copilot.proposal.execution_failed",
                failure,
                proposal_id=
                    proposal_id,
            )

            await self.session.commit()

            if isinstance(
                exc,
                CopilotProposalError,
            ):
                raise

            raise CopilotProposalError(
                "Schedule Engine execution failed: "
                + str(
                    exc
                )
            ) from exc
