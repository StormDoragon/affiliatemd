"use client";

import { FormEvent, useState } from "react";
import { api } from "../../lib/api";

export default function AuthForm({ registrationOpen }: { registrationOpen: boolean }) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = form.get("email");
    const password = form.get("password");
    setError("");
    setNotice("");
    setBusy(true);
    try {
      if (register) {
        await api("users/register", { email, password, full_name: form.get("full_name") });
        setRegister(false);
        setNotice("Account created. Sign in to open your workspace.");
      } else {
        await api("users/token", { email, password });
        window.location.assign("/dashboard");
      }
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>{register ? "Create your account" : "Sign in"}</h1>
      <form onSubmit={submit} className="fields">
        {register && <label>Full name<input name="full_name" autoComplete="name" maxLength={255} required /></label>}
        <label>Email<input name="email" type="email" autoComplete="email" maxLength={254} required /></label>
        <label>Password<input name="password" type="password" minLength={register ? 12 : 1}
          maxLength={128} autoComplete={register ? "new-password" : "current-password"} required /></label>
        <button className="button button-primary" disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
      </form>
      {notice && <p role="status">{notice}</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {registrationOpen && <button type="button" className="link-button" disabled={busy}
        onClick={() => { setRegister(!register); setError(""); setNotice(""); }}>
        {register ? "Use an existing account" : "Create an account"}
      </button>}
    </>
  );
}
