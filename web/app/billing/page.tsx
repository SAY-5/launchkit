"use client";

import { useEffect, useState } from "react";
import { apiFetch, type CurrentUser } from "@/lib/api";

export default function BillingPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch<CurrentUser>("/auth/me")
      .then(setUser)
      .catch(() => setError("Please sign in to manage billing."));
  }, []);

  async function upgrade() {
    setBusy(true);
    setError(null);
    try {
      const res = await apiFetch<{ checkout_url: string }>("/billing/checkout", {
        method: "POST",
      });
      window.location.href = res.checkout_url;
    } catch {
      setError("Checkout is not available. Configure Stripe to enable upgrades.");
      setBusy(false);
    }
  }

  if (error && !user) {
    return (
      <main className="section">
        <p className="error">{error}</p>
      </main>
    );
  }

  const active = user?.subscription_status === "active";

  return (
    <main className="section">
      <h2>Billing</h2>
      <div className="card" style={{ maxWidth: 460 }}>
        <h3>Pro plan</h3>
        <p className="muted">Unlimited notes and the full feature set.</p>
        <p style={{ margin: "12px 0" }}>
          Current status:{" "}
          <span className={`badge ${active ? "badge-active" : "badge-inactive"}`}>
            {user?.subscription_status ?? "unknown"}
          </span>
        </p>
        <button className="btn btn-primary" onClick={upgrade} disabled={busy || active}>
          {active ? "You are on Pro" : busy ? "Redirecting..." : "Upgrade to Pro"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    </main>
  );
}
