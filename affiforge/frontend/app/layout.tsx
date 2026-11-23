import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AffiForge",
  description: "Plan affiliate content, publish to WordPress, and track your reported earnings.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
