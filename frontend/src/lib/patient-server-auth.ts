import {
  cookies,
} from "next/headers";


export function backendBaseUrl() {
  return (
    process.env.BACKEND_URL
    ??
    "http://127.0.0.1:8000"
  ).replace(
    /\/$/,
    "",
  );
}


export async function patientAuthorization() {

  const store =
    await cookies();

  const token =
    store.get(
      "medibook_session",
    )?.value;

  if (!token) {
    return null;
  }

  return {
    Authorization:
      `Bearer ${token}`,
  };
}
