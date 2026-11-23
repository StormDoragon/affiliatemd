import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { backend, SESSION_COOKIE } from "../../lib/backend";
import Workspace from "./workspace";

export const metadata = { robots: { index: false, follow: false } };

export default async function DashboardPage() {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) redirect("/sign-in");

  let account: Response | undefined;
  try {
    account = await backend("/users/me", { headers: { Authorization: `Bearer ${token}` } });
  } catch {
    // A saved session can be retried during an outage.
  }
  if (account?.status === 401) redirect("/sign-in");
  if (!account?.ok) {
    return <main className="page"><section className="hero"><h1>Workspace unavailable</h1>
      <p>Try again shortly.</p><a className="button button-primary" href="/dashboard">Reload workspace</a>
    </section></main>;
  }
  const user = await account.json() as { full_name: string };
  return <Workspace name={user.full_name} demo={process.env.DEMO_MODE === "true"} />;
}
