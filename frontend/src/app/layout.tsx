import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Buildra — AI Software Factory",
  description: "Turn your product requirements into working software, automatically.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>{children}</body>
    </html>
  );
}
