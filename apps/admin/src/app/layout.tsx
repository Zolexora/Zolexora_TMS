import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zolexora Platform Admin",
  description: "Platform operations and tenant administration for Zolexora TMS.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
