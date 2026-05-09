import Link from "next/link";

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">AffiForge</p>
        <h1>Grow affiliate revenue without a complicated setup.</h1>
        <p>
          One guided workflow helps you discover topics, publish content, and track
          earnings from a single dashboard.
        </p>
        <div className="hero-actions">
          <Link href="/dashboard" className="button button-primary">
            Start First Workflow
          </Link>
          <Link href="/dashboard" className="button button-secondary">
            View Dashboard
          </Link>
        </div>
        <ol className="quick-steps">
          <li>Connect your site and affiliate tag.</li>
          <li>Generate a focused content plan from real audience questions.</li>
          <li>Track revenue and repeat what works.</li>
        </ol>
      </section>
    </main>
  );
}
