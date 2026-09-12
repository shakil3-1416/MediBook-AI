import asyncio
import os
from datetime import date, timedelta, time
from decimal import Decimal
from uuid import uuid4

import asyncpg
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing."
    )

DSN = DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql://",
)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

CITY_CONFIG = {

    "Dhaka": {
        "count": 150,
        "areas": [
            "Dhanmondi",
            "Gulshan",
            "Banani",
            "Mirpur",
            "Uttara",
            "Mohammadpur",
            "Bashundhara",
            "Badda",
            "Farmgate",
            "Shahbagh",
            "Malibagh",
            "Rampura",
        ],
    },

    "Chattogram": {
        "count": 70,
        "areas": [
            "GEC Circle",
            "Panchlaish",
            "Agrabad",
            "Nasirabad",
            "Khulshi",
            "Halishahar",
        ],
    },

    "Rajshahi": {
        "count": 45,
        "areas": [
            "Boalia",
            "Kazla",
            "Shaheb Bazar",
            "Laxmipur",
            "Sopura",
        ],
    },

    "Khulna": {
        "count": 45,
        "areas": [
            "Sonadanga",
            "Khalishpur",
            "Boyra",
            "Shibbari",
            "Daulatpur",
        ],
    },

    "Sylhet": {
        "count": 40,
        "areas": [
            "Zindabazar",
            "Ambarkhana",
            "Subidbazar",
            "Mirabazar",
            "Shibganj",
        ],
    },

    "Rangpur": {
        "count": 35,
        "areas": [
            "Dhap",
            "Jahaj Company",
            "Modern Mor",
            "Medical Mor",
        ],
    },

    "Barishal": {
        "count": 30,
        "areas": [
            "Sadar Road",
            "Nathullabad",
            "Band Road",
            "Rupatali",
        ],
    },

    "Mymensingh": {
        "count": 30,
        "areas": [
            "Charpara",
            "Maskanda",
            "Ganginarpar",
            "Town Hall",
        ],
    },

    "Cumilla": {
        "count": 30,
        "areas": [
            "Kandirpar",
            "Tomsom Bridge",
            "Jhautola",
            "Shashongacha",
        ],
    },

    "Gazipur": {
        "count": 25,
        "areas": [
            "Joydebpur",
            "Tongi",
            "Board Bazar",
            "Konabari",
        ],
    },
}


assert (
    sum(
        config["count"]
        for config
        in CITY_CONFIG.values()
    )
    == 500
)


# ============================================================
# SPECIALTIES
# ============================================================

SPECIALTIES = [
    "Cardiology",
    "Dermatology",
    "Neurology",
    "Pediatrics",
    "Gynecology",
    "Orthopedics",
    "Internal Medicine",
    "ENT",
    "Ophthalmology",
    "Psychiatry",
    "Gastroenterology",
    "Urology",
    "Nephrology",
    "Endocrinology",
    "Pulmonology",
    "General Surgery",
    "Oncology",
    "Rheumatology",
]


# Weighted cycle — common outpatient specialties appear more often.

SPECIALTY_CYCLE = [
    "Internal Medicine",
    "Cardiology",
    "Dermatology",
    "Pediatrics",
    "Gynecology",
    "Orthopedics",
    "ENT",
    "Neurology",
    "Ophthalmology",
    "Gastroenterology",
    "Cardiology",
    "Internal Medicine",
    "Dermatology",
    "Pediatrics",
    "Endocrinology",
    "Urology",
    "Nephrology",
    "Pulmonology",
    "Psychiatry",
    "General Surgery",
    "Orthopedics",
    "Gynecology",
    "Oncology",
    "Rheumatology",
]


# ============================================================
# SYNTHETIC DOCTOR NAMES
# ============================================================

FEMALE_FIRST = [
    "Ayesha",
    "Nusrat",
    "Farhana",
    "Sadia",
    "Tasnim",
    "Nabila",
    "Maliha",
    "Rafia",
    "Samira",
    "Nafisa",
    "Fariha",
    "Sumaiya",
    "Mahjabin",
    "Sharmin",
    "Afroza",
    "Tanjina",
    "Mim",
    "Tahmina",
    "Sabrina",
    "Ishrat",
    "Nazia",
    "Anika",
    "Mehjabin",
    "Bushra",
    "Lamia",
]


MALE_FIRST = [
    "Hasan",
    "Arif",
    "Tanvir",
    "Mahmud",
    "Rafiq",
    "Imran",
    "Nayeem",
    "Fahim",
    "Sakib",
    "Ashraf",
    "Rakib",
    "Sabbir",
    "Shahriar",
    "Reza",
    "Adnan",
    "Masud",
    "Zahid",
    "Faisal",
    "Rashed",
    "Noman",
    "Saif",
    "Jahid",
    "Tareq",
    "Moin",
    "Shakil",
]


SURNAMES = [
    "Rahman",
    "Ahmed",
    "Hossain",
    "Islam",
    "Hasan",
    "Khan",
    "Chowdhury",
    "Karim",
    "Mahmud",
    "Kabir",
    "Siddique",
    "Alam",
    "Haque",
    "Sarker",
    "Uddin",
    "Rashid",
    "Amin",
    "Bari",
    "Anwar",
    "Jahan",
]


NAME_POOL = []

for first in FEMALE_FIRST:

    for last in SURNAMES:

        NAME_POOL.append(
            (
                f"Dr. {first} {last}",
                "female",
            )
        )


for first in MALE_FIRST:

    for last in SURNAMES:

        NAME_POOL.append(
            (
                f"Dr. {first} {last}",
                "male",
            )
        )


assert len(NAME_POOL) >= 500


# ============================================================
# SYNTHETIC HOSPITAL BRANDS
# ============================================================

HOSPITAL_BRANDS = [
    "MediBook Central Hospital",
    "MediBook Specialist Centre",
    "MediBook City Medical",
    "MediBook Health Point",
    "MediBook Family Hospital",
    "MediBook Advanced Care",
    "MediBook Medical Centre",
    "MediBook Community Hospital",
]


# ============================================================
# SLOT TIMES
# ============================================================

SLOT_TIMES = [
    time(9, 0),
    time(10, 0),
    time(11, 0),
    time(15, 0),
    time(16, 0),
    time(17, 0),
    time(17, 30),
    time(18, 0),
    time(18, 30),
    time(19, 0),
]


# Each doctor gets 5 slots/day.
# Shift slot window by doctor index to make schedules diverse.

SLOTS_PER_DOCTOR_PER_DAY = 5
DAYS_AHEAD = 21


# ============================================================
# HELPERS
# ============================================================

async def validate_schema(
    conn,
):

    required_doctor_columns = {
        "id",
        "full_name",
        "gender",
        "qualification",
        "experience_years",
        "specialty_id",
        "clinic_name",
        "clinic_location",
        "consultation_fee",
        "is_active",
    }

    rows = await conn.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'doctors'
        """
    )

    columns = {
        row["column_name"]
        for row in rows
    }

    missing = (
        required_doctor_columns
        - columns
    )

    if missing:

        raise RuntimeError(
            "Doctor schema missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )


async def ensure_specialties(
    conn,
):

    existing = await conn.fetch(
        """
        SELECT id, name
        FROM specialties
        """
    )

    mapping = {
        row["name"]:
            row["id"]
        for row in existing
    }


    for name in SPECIALTIES:

        if name in mapping:
            continue

        specialty_id = uuid4()

        await conn.execute(
            """
            INSERT INTO specialties (
                id,
                name
            )
            VALUES (
                $1,
                $2
            )
            """,
            specialty_id,
            name,
        )

        mapping[
            name
        ] = specialty_id


    return mapping


def consultation_fee(
    city: str,
    specialty: str,
    experience: int,
) -> Decimal:

    city_base = {
        "Dhaka": 900,
        "Chattogram": 850,
        "Rajshahi": 700,
        "Khulna": 700,
        "Sylhet": 750,
        "Rangpur": 650,
        "Barishal": 650,
        "Mymensingh": 650,
        "Cumilla": 650,
        "Gazipur": 700,
    }[
        city
    ]

    specialty_bonus = {
        "Cardiology": 350,
        "Neurology": 350,
        "Oncology": 400,
        "Nephrology": 300,
        "Gastroenterology": 250,
        "Endocrinology": 200,
        "Dermatology": 150,
        "Gynecology": 200,
        "Orthopedics": 200,
    }.get(
        specialty,
        100,
    )

    experience_bonus = (
        experience // 5
    ) * 100

    amount = (
        city_base
        + specialty_bonus
        + experience_bonus
    )

    # clean BDT increments
    amount = (
        round(
            amount / 100
        )
        * 100
    )

    return Decimal(
        amount
    )


# ============================================================
# SEED
# ============================================================

async def main():

    print(
        "Connecting to PostgreSQL..."
    )

    conn = await asyncpg.connect(
        DSN
    )

    try:

        await validate_schema(
            conn
        )


        specialties = (
            await ensure_specialties(
                conn
            )
        )


        existing_rows = await conn.fetch(
            """
            SELECT
                id,
                full_name,
                clinic_name,
                clinic_location
            FROM doctors
            """
        )

        existing = {
            (
                row["full_name"],
                row["clinic_name"],
                row["clinic_location"],
            ):
                row["id"]
            for row
            in existing_rows
        }


        generated_doctors = []

        global_index = 0


        async with conn.transaction():

            for (
                city,
                config,
            ) in CITY_CONFIG.items():

                city_count = (
                    config[
                        "count"
                    ]
                )

                areas = (
                    config[
                        "areas"
                    ]
                )


                for city_index in range(
                    city_count
                ):

                    (
                        doctor_name,
                        gender,
                    ) = NAME_POOL[
                        global_index
                    ]

                    specialty = (
                        SPECIALTY_CYCLE[
                            global_index
                            % len(
                                SPECIALTY_CYCLE
                            )
                        ]
                    )

                    area = areas[
                        city_index
                        % len(
                            areas
                        )
                    ]

                    hospital_brand = (
                        HOSPITAL_BRANDS[
                            (
                                city_index
                                // len(
                                    areas
                                )
                            )
                            % len(
                                HOSPITAL_BRANDS
                            )
                        ]
                    )

                    clinic_name = (
                        f"{hospital_brand} "
                        f"— {area}"
                    )

                    clinic_location = (
                        f"{area}, {city}"
                    )

                    experience = (
                        3
                        + (
                            global_index
                            * 7
                        )
                        % 33
                    )

                    qualification = (
                        "MBBS, FCPS "
                        f"({specialty})"
                    )

                    fee = consultation_fee(
                        city,
                        specialty,
                        experience,
                    )


                    key = (
                        doctor_name,
                        clinic_name,
                        clinic_location,
                    )


                    doctor_id = (
                        existing.get(
                            key
                        )
                    )


                    if (
                        doctor_id
                        is None
                    ):

                        doctor_id = uuid4()

                        await conn.execute(
                            """
                            INSERT INTO doctors (
                                id,
                                full_name,
                                gender,
                                qualification,
                                experience_years,
                                specialty_id,
                                clinic_name,
                                clinic_location,
                                consultation_fee,
                                is_active
                            )
                            VALUES (
                                $1,
                                $2,
                                $3,
                                $4,
                                $5,
                                $6,
                                $7,
                                $8,
                                $9,
                                TRUE
                            )
                            """,
                            doctor_id,
                            doctor_name,
                            gender,
                            qualification,
                            experience,
                            specialties[
                                specialty
                            ],
                            clinic_name,
                            clinic_location,
                            fee,
                        )


                    generated_doctors.append(
                        {
                            "id":
                                doctor_id,

                            "city":
                                city,

                            "area":
                                area,

                            "specialty":
                                specialty,

                            "name":
                                doctor_name,
                        }
                    )


                    global_index += 1


        print(
            f"Doctor network ready: "
            f"{len(generated_doctors)}"
        )


        # -----------------------------------------------------
        # Existing future slot lookup
        # -----------------------------------------------------

        doctor_ids = [
            doctor["id"]
            for doctor
            in generated_doctors
        ]

        existing_slot_rows = await conn.fetch(
            """
            SELECT
                doctor_id,
                slot_date,
                start_time
            FROM doctor_slots
            WHERE doctor_id = ANY($1::uuid[])
              AND slot_date >= CURRENT_DATE
              AND slot_date <= CURRENT_DATE + $2
            """,
            doctor_ids,
            DAYS_AHEAD + 1,
        )


        existing_slots = {
            (
                row[
                    "doctor_id"
                ],
                row[
                    "slot_date"
                ],
                row[
                    "start_time"
                ],
            )
            for row
            in existing_slot_rows
        }


        slots_to_insert = []

        today = date.today()


        for index, doctor in enumerate(
            generated_doctors
        ):

            # Different doctors use different windows
            # so everyone does not have identical schedules.

            start_offset = (
                index
                % (
                    len(SLOT_TIMES)
                    - SLOTS_PER_DOCTOR_PER_DAY
                    + 1
                )
            )

            doctor_times = (
                SLOT_TIMES[
                    start_offset:
                    start_offset
                    + SLOTS_PER_DOCTOR_PER_DAY
                ]
            )


            for day_offset in range(
                1,
                DAYS_AHEAD + 1,
            ):

                slot_date = (
                    today
                    + timedelta(
                        days=day_offset
                    )
                )


                # Make Sundays lighter:
                if (
                    slot_date.weekday()
                    == 6
                    and index % 3
                    != 0
                ):
                    continue


                for slot_time in (
                    doctor_times
                ):

                    key = (
                        doctor["id"],
                        slot_date,
                        slot_time,
                    )

                    if key in existing_slots:
                        continue


                    slots_to_insert.append(
                        (
                            uuid4(),
                            doctor[
                                "id"
                            ],
                            slot_date,
                            slot_time,
                            True,
                        )
                    )


        if slots_to_insert:

            print(
                "Creating",
                len(
                    slots_to_insert
                ),
                "future appointment slots..."
            )

            await conn.executemany(
                """
                INSERT INTO doctor_slots (
                    id,
                    doctor_id,
                    slot_date,
                    start_time,
                    is_available
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5
                )
                """,
                slots_to_insert,
            )


        # -----------------------------------------------------
        # Dynamic cluster view
        # -----------------------------------------------------

        await conn.execute(
            """
            CREATE OR REPLACE VIEW
            doctor_city_clusters
            AS
            SELECT
                TRIM(
                    SPLIT_PART(
                        clinic_location,
                        ',',
                        2
                    )
                ) AS city,

                COUNT(*) AS doctor_count,

                COUNT(
                    DISTINCT clinic_name
                ) AS hospital_count,

                COUNT(
                    DISTINCT specialty_id
                ) AS specialty_count

            FROM doctors

            WHERE is_active = TRUE

            GROUP BY
                TRIM(
                    SPLIT_PART(
                        clinic_location,
                        ',',
                        2
                    )
                );
            """
        )


        print()
        print(
            "=========================================="
        )
        print(
            "CITY DISTRIBUTION"
        )
        print(
            "=========================================="
        )


        city_rows = await conn.fetch(
            """
            SELECT
                city,
                doctor_count,
                hospital_count,
                specialty_count
            FROM doctor_city_clusters
            ORDER BY doctor_count DESC
            """
        )


        for row in city_rows:

            print(
                f"{row['city']:<15} "
                f"Doctors={row['doctor_count']:<4} "
                f"Hospitals={row['hospital_count']:<4} "
                f"Specialties={row['specialty_count']}"
            )


        print()
        print(
            "=========================================="
        )
        print(
            "NETWORK TOTALS"
        )
        print(
            "=========================================="
        )


        totals = await conn.fetchrow(
            """
            SELECT

                COUNT(*) FILTER (
                    WHERE is_active = TRUE
                ) AS doctors,

                COUNT(
                    DISTINCT clinic_name
                ) FILTER (
                    WHERE is_active = TRUE
                ) AS hospitals,

                COUNT(
                    DISTINCT specialty_id
                ) FILTER (
                    WHERE is_active = TRUE
                ) AS specialties

            FROM doctors
            """
        )


        slot_total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM doctor_slots
            WHERE slot_date > CURRENT_DATE
              AND is_available = TRUE
            """
        )


        print(
            "Active doctors:     ",
            totals[
                "doctors"
            ],
        )

        print(
            "Hospitals/clinics:  ",
            totals[
                "hospitals"
            ],
        )

        print(
            "Specialties:        ",
            totals[
                "specialties"
            ],
        )

        print(
            "Future open slots:  ",
            slot_total,
        )


        print()
        print(
            "NATIONAL DIRECTORY SEED: GREEN"
        )


    finally:

        await conn.close()


if __name__ == "__main__":

    asyncio.run(
        main()
    )
