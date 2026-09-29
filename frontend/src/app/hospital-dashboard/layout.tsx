import {
  ReactNode,
} from "react";

import {
  HospitalOperationsShell,
} from "@/components/hospital/hospital-operations-shell";


export default function HospitalDashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <HospitalOperationsShell>
      {children}
    </HospitalOperationsShell>
  );
}
