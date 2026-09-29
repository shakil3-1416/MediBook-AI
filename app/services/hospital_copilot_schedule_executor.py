from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.schemas.hospital_schedule_engine import (
    ScheduleRuleUpdate as ScheduleRuleUpdate,
)

from app.schemas.hospital_schedule_engine import (
    ScheduleExceptionCreate as ScheduleExceptionCreate,
)


class CopilotScheduleExecutionError(
    RuntimeError
):
    pass


def _serialize(
    value: Any,
) -> dict[str, Any]:
    if hasattr(
        value,
        "model_dump",
    ):
        result = value.model_dump(
            mode="json"
        )

        if isinstance(
            result,
            dict,
        ):
            return result

    if isinstance(
        value,
        dict,
    ):
        return value

    return {
        "result":
            str(
                value
            ),
    }


def _uuid(
    value: Any,
    *,
    label: str,
) -> UUID:
    try:
        return UUID(
            str(
                value
            )
        )

    except Exception as exc:
        raise CopilotScheduleExecutionError(
            f"{label} is not a valid UUID."
        ) from exc


class HospitalCopilotScheduleExecutor:
    """
    Deterministic adapter around the existing
    hospital Schedule Engine API handlers.

    Important:
    - no direct schedule-table INSERT/UPDATE/DELETE
    - no LLM-generated mutation payload
    - hospital authorization remains inside the existing
      schedule handlers
    - doctor_id is taken from the deterministic proposal
      impact calculated before confirmation
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        hospital_id,
        hospital_slug: str,
        current_user,
    ) -> None:
        self.session = session

        self.hospital_id = str(
            hospital_id
        )

        self.hospital_slug = (
            hospital_slug
        )

        self.current_user = (
            current_user
        )


    @staticmethod
    def _doctor_id(
        impact: dict[
            str,
            Any,
        ],
    ) -> UUID:
        value = impact.get(
            "doctor_id"
        )

        if value is None:
            raise CopilotScheduleExecutionError(
                "Proposal impact does not contain doctor_id."
            )

        return _uuid(
            value,
            label="doctor_id",
        )


    async def execute_capacity_change(
        self,
        payload: dict[
            str,
            Any,
        ],
        impact: dict[
            str,
            Any,
        ],
    ) -> dict[
        str,
        Any,
    ]:
        from app.api.v1.hospital_schedules import (
            update_rule,
        )

        doctor_id = self._doctor_id(
            impact
        )

        rule_id = _uuid(
            payload.get(
                "schedule_rule_id"
            ),
            label="schedule_rule_id",
        )

        try:
            new_capacity = int(
                payload[
                    "new_capacity"
                ]
            )

        except Exception as exc:
            raise CopilotScheduleExecutionError(
                "new_capacity is invalid."
            ) from exc


        request = ScheduleRuleUpdate(
            capacity=new_capacity
        )


        result = await update_rule(
            hospital_slug=
                self.hospital_slug,

            doctor_id=
                doctor_id,

            rule_id=
                rule_id,

            payload=
                request,

            current_user=
                self.current_user,

            session=
                self.session,
        )


        return {
            "action":
                "schedule_capacity_change",

            "doctor_id":
                str(
                    doctor_id
                ),

            "schedule_rule_id":
                str(
                    rule_id
                ),

            "new_capacity":
                new_capacity,

            "schedule_engine":
                _serialize(
                    result
                ),
        }


    async def execute_closure(
        self,
        payload: dict[
            str,
            Any,
        ],
        impact: dict[
            str,
            Any,
        ],
    ) -> dict[
        str,
        Any,
    ]:
        from app.api.v1.hospital_schedules import (
            create_exception,
        )

        doctor_id = self._doctor_id(
            impact
        )


        try:
            closure_date = (
                date.fromisoformat(
                    str(
                        payload[
                            "date"
                        ]
                    )
                )
            )

        except Exception as exc:
            raise CopilotScheduleExecutionError(
                "Closure date must use YYYY-MM-DD."
            ) from exc


        exception_payload: dict[
            str,
            Any,
        ] = {
            'exception_date':
                closure_date,
        }

        exception_payload[
            'kind'
        ] = 'closure'

        exception_payload[
            'reason'
        ] = str(
            payload.get(
                "reason"
            )
            or "Copilot confirmed closure"
        )


        request = ScheduleExceptionCreate(
            **exception_payload
        )


        result = await create_exception(
            hospital_slug=
                self.hospital_slug,

            doctor_id=
                doctor_id,

            payload=
                request,

            current_user=
                self.current_user,

            session=
                self.session,
        )


        return {
            "action":
                "schedule_closure",

            "doctor_id":
                str(
                    doctor_id
                ),

            "date":
                closure_date.isoformat(),

            "reason":
                str(
                    payload.get(
                        "reason"
                    )
                    or ""
                ),

            "schedule_engine":
                _serialize(
                    result
                ),
        }
