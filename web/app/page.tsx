import Link from "next/link";

export default function Home() {
  return (
    <main>
      <section className="hero">
        <h1>Ship your SaaS from day one</h1>
        <p>
          LaunchKit gives you sign-up, tenant-scoped data, Stripe billing, and a working
          in-product feature, so the first customer can sign up and start using your app today.
        </p>
        <div className="cta-row">
          <Link href="/signup" className="btn btn-primary">
            Create an account
          </Link>
          <Link href="/signin" className="btn">
            Sign in
          </Link>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h3>Accounts and teams</h3>
          <p>Every user belongs to an organization, and every record stays inside it.</p>
        </div>
        <div className="card">
          <h3>Billing built in</h3>
          <p>Upgrade through Stripe Checkout and let subscription state follow the webhook.</p>
        </div>
        <div className="card">
          <h3>A real feature</h3>
          <p>Summarize a note through a provider seam you can swap for your own backend.</p>
        </div>
      </section>
    </main>
  );
}
