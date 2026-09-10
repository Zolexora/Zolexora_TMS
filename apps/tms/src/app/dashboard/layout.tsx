import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Customer Dashboard | Zolexora TMS",
  description: "Operational dashboard for transport teams.",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
