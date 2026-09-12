import axios from "axios";

import type {
  AppointmentListResponse,
  AvailabilityResponse,
  ChatResponse,
  DoctorListResponse,
} from "@/types/api";


export const api = axios.create({
  baseURL:
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1",

  headers: {
    "Content-Type": "application/json",
  },

  timeout: 30000,
});


export async function getDoctors(
  params?: {
    specialty?: string;
    location?: string;
    gender?: string;
    max_fee?: number;
    name?: string;
  }
): Promise<DoctorListResponse> {
  const { data } =
    await api.get<DoctorListResponse>(
      "/doctors",
      {
        params,
      }
    );

  return data;
}


export async function getDoctorAvailability(
  doctorId: string,
  date: string
): Promise<AvailabilityResponse> {
  const { data } =
    await api.get<AvailabilityResponse>(
      `/availability/doctors/${doctorId}`,
      {
        params: {
          date,
        },
      }
    );

  return data;
}


export async function sendChatMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const { data } =
    await api.post<ChatResponse>(
      "/chat",
      {
        message,
        conversation_id:
          conversationId ?? null,
      }
    );

  return data;
}


export async function getAppointments(
  phone: string
): Promise<AppointmentListResponse> {
  const { data } =
    await api.get<AppointmentListResponse>(
      "/appointments",
      {
        params: {
          phone,
        },
      }
    );

  return data;
}
