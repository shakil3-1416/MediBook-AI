import "server-only";

import { cookies } from "next/headers";

export const ACTIVE_HOSPITAL_COOKIE = "medibook_active_hospital";
export const PATIENT_HOSPITAL_COOKIE = "medibook_patient_hospital";

/*
 * Which hospital a staff request is for. An explicit ?hospital= value wins;
 * otherwise the workspace chosen in the dashboard, which is stored in a
 * cookie. The backend still checks that the user belongs to that hospital.
 */
export async function activeHospitalSlug(
  requested?: string | null,
): Promise<string | null> {
  const explicit = requested?.trim();
  if (explicit) {
    return explicit;
  }
  const stored = (await cookies()).get(ACTIVE_HOSPITAL_COOKIE)?.value?.trim();
  return stored || null;
}

/*
 * Which hospital a patient request is for: an explicit ?hospital= value,
 * then the hospital whose assistant the patient opened last, then the
 * configured default.
 */
export async function patientHospitalSlug(
  requested?: string | null,
): Promise<string> {
  const explicit = requested?.trim();
  if (explicit) {
    return explicit;
  }
  const remembered = (await cookies()).get(PATIENT_HOSPITAL_COOKIE)?.value?.trim();
  if (remembered) {
    return remembered;
  }
  return process.env.MEDIBOOK_DEFAULT_HOSPITAL_SLUG?.trim() || "medibook-demo";
}

/*
 * Session token for staff and platform pages. Platform admins may sign in
 * on either sign-in page, so both session cookies are accepted; the
 * backend decides what the token is allowed to see.
 */
export async function staffSessionToken(): Promise<string | null> {
  const store = await cookies();
  return (
    store.get("medibook_hospital_session")?.value ??
    store.get("medibook_access_token")?.value ??
    store.get("medibook_session")?.value ??
    null
  );
}
