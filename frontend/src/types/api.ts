export interface Specialty {
  id: string;
  name: string;
}

export interface Doctor {
  id: string;
  full_name: string;
  gender: string | null;
  qualification: string | null;
  experience_years: number;
  specialty: Specialty;
  clinic_name: string;
  clinic_location: string;
  consultation_fee: string;
}

export interface DoctorListResponse {
  count: number;
  doctors: Doctor[];
}

export type ChatActionType =
  | "send_message"
  | "book_slot"
  | "confirm"
  | "cancel"
  | "reschedule";

export type ChatActionVariant =
  | "primary"
  | "secondary"
  | "danger";

export interface ChatAction {
  id: string;
  type: ChatActionType;
  label: string;
  message: string;
  variant: ChatActionVariant;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  actions: ChatAction[];
}

export interface AvailabilityResponse {
  found: boolean;
  doctor?: {
    id: string;
    full_name: string;
    specialty: string;
    clinic_name: string;
    clinic_location: string;
    consultation_fee: number;
  };
  date?: string;
  available_slots?: string[];
  count?: number;
}

export interface Appointment {
  appointment_id: string;
  confirmation_code: string;
  status: string;

  doctor: {
    id: string;
    name: string;
    specialty: string;
    clinic_name: string;
    clinic_location: string;
  };

  date: string;
  time: string;
  consultation_fee: number;
}

export interface AppointmentListResponse {
  count: number;
  appointments: Appointment[];
}
