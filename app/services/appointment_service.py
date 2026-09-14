from app.models.hospital import HospitalDoctor
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment
from app.models.appointment_event import AppointmentEvent
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.schedule import DoctorSlot


ACTIVE_STATUSES = {
    "confirmed",
    "checked_in",
}


class BookingError(Exception):
    pass


class SlotNotFoundError(BookingError):
    pass


class SlotUnavailableError(BookingError):
    pass


class AppointmentNotFoundError(BookingError):
    pass


class AppointmentStateError(BookingError):
    pass


class PatientValidationError(BookingError):
    pass


class AppointmentService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # ========================================================
    # Helpers
    # ========================================================

    async def get_or_create_patient(
        self,
        *,
        full_name: str,
        phone: str,
    ) -> Patient:

        full_name = full_name.strip()
        phone = phone.strip()

        if len(full_name) < 2:
            raise PatientValidationError(
                "Patient name is invalid."
            )

        if len(phone) < 8:
            raise PatientValidationError(
                "Patient phone is invalid."
            )

        patient = await self.session.scalar(
            select(Patient).where(
                Patient.phone == phone
            )
        )

        if patient:
            if patient.full_name != full_name:
                patient.full_name = full_name

            return patient

        patient = Patient(
            full_name=full_name,
            phone=phone,
        )

        self.session.add(patient)

        await self.session.flush()

        return patient

    async def add_event(
        self,
        *,
        appointment_id: UUID,
        event_type: str,
        payload: dict,
    ) -> None:

        self.session.add(
            AppointmentEvent(
                appointment_id=appointment_id,
                event_type=event_type,
                payload=payload,
            )
        )

    async def active_slot_count(
        self,
        *,
        slot_id: UUID,
        exclude_appointment_id: UUID | None = None,
    ) -> int:
        statement = select(
            func.count(Appointment.id)
        ).where(
            Appointment.doctor_slot_id == slot_id,
            Appointment.status.in_(ACTIVE_STATUSES),
        )

        if exclude_appointment_id is not None:
            statement = statement.where(
                Appointment.id != exclude_appointment_id
            )

        value = await self.session.scalar(statement)

        return int(value or 0)

    async def refresh_slot_availability(
        self,
        *,
        slot: DoctorSlot,
    ) -> int:
        active = await self.active_slot_count(
            slot_id=slot.id,
        )

        slot.is_available = bool(
            slot.is_enabled
            and active < slot.capacity
        )

        return active

    # ========================================================
    # Booking preview
    # ========================================================

    async def preview_booking(
        self,
        *,
        slot_id: UUID,
        hospital_id: UUID,
    ) -> dict:

        slot = await self.session.scalar(
            select(DoctorSlot)
            .join(
                HospitalDoctor,
                HospitalDoctor.id
                == DoctorSlot.hospital_doctor_id,
            )
            .options(
                selectinload(
                    DoctorSlot.doctor
                ).selectinload(
                    Doctor.specialty
                )
            )
            .where(
                DoctorSlot.id == slot_id,
                DoctorSlot.is_enabled.is_(True),
                HospitalDoctor.hospital_id
                == hospital_id,
                HospitalDoctor.is_active.is_(True),
            )
        )

        if slot is None:
            raise SlotNotFoundError(
                "Appointment slot does not exist."
            )

        if not slot.is_available:
            raise SlotUnavailableError(
                "Appointment slot is unavailable."
            )

        doctor = slot.doctor

        return {
            "hospital_id": str(hospital_id),
            "slot_id": str(slot.id),
            "doctor_id": str(doctor.id),
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty.name,
            "clinic_name": doctor.clinic_name,
            "clinic_location": doctor.clinic_location,
            "consultation_fee": float(
                doctor.consultation_fee
            ),
            "date": slot.slot_date.isoformat(),
            "time": slot.start_time.strftime(
                "%H:%M"
            ),
        }

    # ========================================================
    # Confirm booking
    # ========================================================

    async def confirm_booking(
        self,
        *,
        slot_id: UUID,
        hospital_id: UUID,
        patient_name: str,
        patient_phone: str,
    ) -> dict:

        async with self.session.begin():

            slot = await self.session.scalar(
                select(DoctorSlot)
                .join(
                    HospitalDoctor,
                    HospitalDoctor.doctor_id
                    == DoctorSlot.doctor_id,
                )
                .options(
                    selectinload(
                        DoctorSlot.doctor
                    )
                )
                .where(
                    DoctorSlot.id == slot_id,
                    HospitalDoctor.hospital_id
                    == hospital_id,
                )
                .with_for_update()
            )

            if slot is None:
                raise SlotNotFoundError(
                    "Appointment slot does not exist."
                )

            if not slot.is_enabled:
                raise SlotUnavailableError(
                    "This appointment slot is disabled."
                )

            active_count = await self.active_slot_count(
                slot_id=slot.id,
            )

            if active_count >= slot.capacity:
                slot.is_available = bool(
                slot.is_enabled
                and active_count + 1 < slot.capacity
            )

                raise SlotUnavailableError(
                    "This appointment time has reached capacity."
                )

            patient = await self.get_or_create_patient(
                full_name=patient_name,
                phone=patient_phone,
            )

            code = (
                "MED-"
                + uuid4().hex[:10].upper()
            )

            appointment = Appointment(
                doctor_id=slot.doctor_id,
                doctor_slot_id=slot.id,
                patient_id=patient.id,
                hospital_id=hospital_id,
                consultation_fee=Decimal(
                    str(
                        slot.doctor.consultation_fee
                    )
                ),
                status="confirmed",
                confirmation_code=code,
                booked_at=datetime.now(
                    timezone.utc
                ),
            )

            self.session.add(
                appointment
            )

            slot.is_available = False

            await self.session.flush()

            await self.refresh_slot_availability(
                slot=slot,
            )

            await self.add_event(
                appointment_id=appointment.id,
                event_type="created",
                payload={
                    "slot_id": str(slot.id),
                    "doctor_id": str(
                        slot.doctor_id
                    ),
                    "date": (
                        slot.slot_date.isoformat()
                    ),
                    "time": (
                        slot.start_time.strftime(
                            "%H:%M"
                        )
                    ),
                },
            )

            appointment_id = appointment.id
            doctor_name = slot.doctor.full_name
            clinic_name = slot.doctor.clinic_name
            fee = float(
                slot.doctor.consultation_fee
            )
            appointment_date = (
                slot.slot_date.isoformat()
            )
            appointment_time = (
                slot.start_time.strftime(
                    "%H:%M"
                )
            )

        return {
            "hospital_id": str(hospital_id),
            "appointment_id": str(
                appointment_id
            ),
            "confirmation_code": code,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "doctor_name": doctor_name,
            "date": appointment_date,
            "time": appointment_time,
            "clinic_name": clinic_name,
            "consultation_fee": fee,
            "status": "confirmed",
        }

    # ========================================================
    # List patient's appointments
    # ========================================================

    async def list_for_phone(
        self,
        *,
        phone: str,
        hospital_id: UUID,
        include_cancelled: bool = False,
    ) -> list[dict]:

        statement = (
            select(Appointment)
            .join(
                Patient,
                Patient.id
                == Appointment.patient_id,
            )
            .options(
                selectinload(
                    Appointment.slot
                ),
                selectinload(
                    Appointment.doctor
                ).selectinload(
                    Doctor.specialty
                ),
            )
            .where(
                Patient.phone == phone,
                Appointment.hospital_id
                == hospital_id,
            )
        )

        if not include_cancelled:
            statement = statement.where(
                Appointment.status.in_(
                    ACTIVE_STATUSES
                )
            )

        statement = statement.order_by(
            Appointment.booked_at.desc()
        )

        appointments = list(
            (
                await self.session.execute(
                    statement
                )
            )
            .scalars()
            .unique()
            .all()
        )

        return [
            self.serialize_appointment(
                appointment
            )
            for appointment in appointments
        ]

    # ========================================================
    # Find by confirmation code
    # ========================================================

    async def get_by_confirmation(
        self,
        confirmation_code: str,
    ) -> Appointment | None:

        return await self.session.scalar(
            select(Appointment)
            .options(
                selectinload(
                    Appointment.slot
                ),
                selectinload(
                    Appointment.doctor
                ).selectinload(
                    Doctor.specialty
                ),
                selectinload(
                    Appointment.patient
                ),
            )
            .where(
                Appointment.confirmation_code
                == confirmation_code.upper()
            )
        )

    # ========================================================
    # Cancellation
    # ========================================================

    async def cancel_appointment(
        self,
        *,
        confirmation_code: str,
        patient_phone: str,
        hospital_id: UUID,
    ) -> dict:

        async with self.session.begin():

            appointment = await self.session.scalar(
                select(Appointment)
                .join(
                    Patient,
                    Patient.id
                    == Appointment.patient_id,
                )
                .options(
                    selectinload(
                        Appointment.slot
                    ),
                    selectinload(
                        Appointment.doctor
                    ),
                )
                .where(
                    Appointment.confirmation_code
                    == confirmation_code.upper(),
                    Patient.phone
                    == patient_phone,
                    Appointment.hospital_id
                    == hospital_id,
                )
                .with_for_update()
            )

            if appointment is None:
                raise AppointmentNotFoundError(
                    "Appointment not found."
                )

            if appointment.status == "cancelled":
                raise AppointmentStateError(
                    "Appointment is already cancelled."
                )

            if appointment.status not in ACTIVE_STATUSES:
                raise AppointmentStateError(
                    "Appointment cannot be cancelled "
                    f"from status {appointment.status}."
                )

            slot = await self.session.scalar(
                select(DoctorSlot)
                .where(
                    DoctorSlot.id
                    == appointment.doctor_slot_id
                )
                .with_for_update()
            )

            old_status = appointment.status

            appointment.status = "cancelled"

            appointment.cancelled_at = (
                datetime.now(
                    timezone.utc
                )
            )

            await self.session.flush()

            if slot is not None:
                await self.refresh_slot_availability(
                    slot=slot,
                )

            await self.add_event(
                appointment_id=appointment.id,
                event_type="cancelled",
                payload={
                    "previous_status": old_status,
                    "slot_id": str(
                        appointment.doctor_slot_id
                    ),
                    "date": (
                        slot.slot_date.isoformat()
                        if slot
                        else None
                    ),
                    "time": (
                        slot.start_time.strftime(
                            "%H:%M"
                        )
                        if slot
                        else None
                    ),
                },
            )

            result = {
                "appointment_id": str(
                    appointment.id
                ),
                "confirmation_code": (
                    appointment.confirmation_code
                ),
                "doctor_name": (
                    appointment.doctor.full_name
                ),
                "status": "cancelled",
                "slot_released": (
                    slot is not None
                ),
            }

        return result

    # ========================================================
    # Reschedule
    # ========================================================

    async def reschedule_appointment(
        self,
        *,
        confirmation_code: str,
        patient_phone: str,
        hospital_id: UUID,
        new_slot_id: UUID,
    ) -> dict:

        async with self.session.begin():

            appointment = await self.session.scalar(
                select(Appointment)
                .join(
                    Patient,
                    Patient.id
                    == Appointment.patient_id,
                )
                .options(
                    selectinload(
                        Appointment.doctor
                    ),
                    selectinload(
                        Appointment.slot
                    ),
                )
                .where(
                    Appointment.confirmation_code
                    == confirmation_code.upper(),
                    Patient.phone
                    == patient_phone,
                    Appointment.hospital_id
                    == hospital_id,
                )
                .with_for_update()
            )

            if appointment is None:
                raise AppointmentNotFoundError(
                    "Appointment not found."
                )

            if appointment.status not in ACTIVE_STATUSES:
                raise AppointmentStateError(
                    "Only active appointments "
                    "can be rescheduled."
                )

            old_slot = await self.session.scalar(
                select(DoctorSlot)
                .where(
                    DoctorSlot.id
                    == appointment.doctor_slot_id
                )
                .with_for_update()
            )

            new_slot = await self.session.scalar(
                select(DoctorSlot)
                .join(
                    HospitalDoctor,
                    HospitalDoctor.doctor_id
                    == DoctorSlot.doctor_id,
                )
                .options(
                    selectinload(
                        DoctorSlot.doctor
                    )
                )
                .where(
                    DoctorSlot.id
                    == new_slot_id,
                    DoctorSlot.is_enabled.is_(True),
                    HospitalDoctor.hospital_id
                    == hospital_id,
                )
                .with_for_update()
            )

            if new_slot is None:
                raise SlotNotFoundError(
                    "New appointment slot not found."
                )

            if not new_slot.is_enabled:
                raise SlotUnavailableError(
                    "The requested new slot is disabled."
                )

            if (
                old_slot is not None
                and old_slot.id == new_slot.id
            ):
                raise AppointmentStateError(
                    "Appointment is already scheduled for this slot."
                )

            destination_count = (
                await self.active_slot_count(
                    slot_id=new_slot.id,
                    exclude_appointment_id=appointment.id,
                )
            )

            if destination_count >= new_slot.capacity:
                new_slot.is_available = False

                raise SlotUnavailableError(
                    "The requested new slot has reached capacity."
                )

            old_payload = {
                "slot_id": str(
                    appointment.doctor_slot_id
                ),
                "doctor_id": str(
                    appointment.doctor_id
                ),
                "date": (
                    old_slot.slot_date.isoformat()
                    if old_slot
                    else None
                ),
                "time": (
                    old_slot.start_time.strftime(
                        "%H:%M"
                    )
                    if old_slot
                    else None
                ),
            }

            appointment.doctor_slot_id = (
                new_slot.id
            )

            appointment.doctor_id = (
                new_slot.doctor_id
            )

            appointment.consultation_fee = Decimal(
                str(
                    new_slot.doctor.consultation_fee
                )
            )

            appointment.cancelled_at = None

            await self.session.flush()

            if old_slot is not None:
                await self.refresh_slot_availability(
                    slot=old_slot,
                )

            await self.refresh_slot_availability(
                slot=new_slot,
            )

            await self.add_event(
                appointment_id=appointment.id,
                event_type="rescheduled",
                payload={
                    "from": old_payload,
                    "to": {
                        "slot_id": str(
                            new_slot.id
                        ),
                        "doctor_id": str(
                            new_slot.doctor_id
                        ),
                        "date": (
                            new_slot.slot_date.isoformat()
                        ),
                        "time": (
                            new_slot.start_time.strftime(
                                "%H:%M"
                            )
                        ),
                    },
                },
            )

            result = {
                "appointment_id": str(
                    appointment.id
                ),
                "confirmation_code": (
                    appointment.confirmation_code
                ),
                "status": (
                    appointment.status
                ),
                "doctor_name": (
                    new_slot.doctor.full_name
                ),
                "clinic_name": (
                    new_slot.doctor.clinic_name
                ),
                "date": (
                    new_slot.slot_date.isoformat()
                ),
                "time": (
                    new_slot.start_time.strftime(
                        "%H:%M"
                    )
                ),
                "consultation_fee": float(
                    new_slot.doctor.consultation_fee
                ),
                "old_slot_released": (
                    old_slot is not None
                ),
            }

        return result

    # ========================================================
    # Serializer
    # ========================================================

    @staticmethod
    def serialize_appointment(
        appointment: Appointment,
    ) -> dict:

        return {
            "appointment_id": str(
                appointment.id
            ),
            "hospital_id": str(
                appointment.hospital_id
            ),
            "confirmation_code": (
                appointment.confirmation_code
            ),
            "status": appointment.status,
            "doctor": {
                "id": str(
                    appointment.doctor.id
                ),
                "name": (
                    appointment.doctor.full_name
                ),
                "specialty": (
                    appointment.doctor.specialty.name
                ),
                "clinic_name": (
                    appointment.doctor.clinic_name
                ),
                "clinic_location": (
                    appointment.doctor.clinic_location
                ),
            },
            "date": (
                appointment.slot.slot_date
                .isoformat()
            ),
            "time": (
                appointment.slot.start_time
                .strftime("%H:%M")
            ),
            "consultation_fee": float(
                appointment.consultation_fee
            ),
        }
