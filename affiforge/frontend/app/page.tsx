import Link from "next/link";

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">AffiForge</p>
        <h1>From audience questions to published posts.</h1>
        <p>Research topics, edit drafts, publish to WordPress, and see which posts earn revenue.</p>
        <div className="hero-actions">
          <Link href="/dashboard" className="button button-primary">Open workspace</Link>
          <Link href="/sign-in" className="button button-secondary">Sign in</Link>
        </div>
      </section>
    </main>
  );
}
