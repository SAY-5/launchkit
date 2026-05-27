import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "LaunchKit",
  description: "Multi-tenant SaaS starter with auth, billing, and a provider-backed feature.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <nav className="nav">
            <Link href="/" className="brand">
              LaunchKit
            </Link>
            <div className="nav-links">
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/billing">Billing</Link>
              <Link href="/signin" className="btn">
                Sign in
              </Link>
            </div>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
