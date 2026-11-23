import Link from "next/link";
import { backend } from "../../lib/backend";
import AuthForm from "./form";

export const metadata = { robots: { index: false, follow: false } };

export default async function SignInPage() {
  let registrationOpen = false;
  try {
    const result = await backend("/users/registration");
    if (result.ok) registrationOpen = (await result.json()).enabled;
  } catch {
    // The form can still surface an availability error when submitted.
  }

  return (
    <main className="page">
      <section className="panel auth-card">
        <Link href="/" className="eyebrow">AffiForge</Link>
        <AuthForm registrationOpen={registrationOpen} />
      </section>
    </main>
  );
}
