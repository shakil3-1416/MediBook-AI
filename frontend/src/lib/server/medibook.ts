import "server-only";


const API_BASE =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  "http://127.0.0.1:8000/api/v1";


export type Specialty = {
  id: string;
  name: string;
};


export type Doctor = {
  id: string;
  full_name: string;
  gender: string;
  qualification: string;
  experience_years: number;
  specialty: Specialty;
  clinic_name: string;
  clinic_location: string;
  consultation_fee: string | number;
};


export type DoctorSearchResponse = {
  count: number;
  doctors: Doctor[];
};


class MediBookServerApiError extends Error {
  status: number;

  constructor(
    message: string,
    status: number,
  ) {
    super(message);
    this.name =
      "MediBookServerApiError";
    this.status = status;
  }
}


async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...init,

      /*
       * Appointment and availability data
       * are dynamic. We start conservatively
       * with no-store and can introduce
       * targeted caching later.
       */
      cache: "no-store",

      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    },
  );

  if (!response.ok) {
    throw new MediBookServerApiError(
      `MediBook API returned ${response.status}`,
      response.status,
    );
  }

  return response.json() as Promise<T>;
}


export async function getDoctors(
  filters?: {
    name?: string;
    specialty?: string;
    location?: string;
    gender?: string;
    maxFee?: string;
  },
): Promise<DoctorSearchResponse> {
  const params =
    new URLSearchParams();

  if (filters?.name) {
    params.set(
      "name",
      filters.name,
    );
  }

  if (filters?.specialty) {
    params.set(
      "specialty",
      filters.specialty,
    );
  }

  if (filters?.location) {
    params.set(
      "location",
      filters.location,
    );
  }

  if (filters?.gender) {
    params.set(
      "gender",
      filters.gender,
    );
  }

  if (filters?.maxFee) {
    params.set(
      "max_fee",
      filters.maxFee,
    );
  }

  const query =
    params.toString();

  return apiFetch<DoctorSearchResponse>(
    `/doctors${query ? `?${query}` : ""}`,
  );
}


export async function getDoctor(
  doctorId: string,
): Promise<Doctor | null> {
  try {
    return await apiFetch<Doctor>(
      `/doctors/${encodeURIComponent(
        doctorId,
      )}`,
    );
  } catch (error) {
    if (
      error instanceof MediBookServerApiError &&
      error.status === 404
    ) {
      return null;
    }

    throw error;
  }
}
