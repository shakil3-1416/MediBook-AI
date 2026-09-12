import {
  NextResponse,
} from "next/server";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function GET() {
  const [
    demo,
    isolation,
  ] =
    await Promise.all([
      fetch(
        `${BACKEND}/api/v1/hospital-public/medibook-demo`,
        {
          cache:
            "no-store",
        },
      ),

      fetch(
        `${BACKEND}/api/v1/hospital-public/medibook-isolation-test`,
        {
          cache:
            "no-store",
        },
      ),
    ]);


  const hospitals =
    [];


  if (demo.ok) {
    hospitals.push(
      await demo.json(),
    );
  }


  if (isolation.ok) {
    hospitals.push(
      await isolation.json(),
    );
  }


  return NextResponse.json({
    hospitals,
    total_hospitals:
      hospitals.length,

    total_doctors:
      hospitals.reduce(
        (
          total,
          hospital,
        ) =>
          total
          +
          (
            hospital
              .doctor_count
            ?? 0
          ),
        0,
      ),
  });
}
