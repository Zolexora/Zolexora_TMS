import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zolexora TMS",
  description: "Complete transport management platform for bookings, duties, fleet, billing, and operations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
