import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PasswordField } from "./password-field";
import { supabase } from "../lib/supabase";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  async function signInWithGoogle() {
    setMessage("");
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) setMessage(error.message);
  }

  async function signInWithPassword() {
    setIsSubmitting(true);
    setMessage("");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setIsSubmitting(false);

    if (error) {
      setMessage("Unable to sign in. Check your email and password, then try again.");
      return;
    }

    navigate("/dashboard");
  }

  return (
    <form 
      className="mx-auto flex w-full max-w-md flex-col gap-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl"
      onSubmit={(event) => { event.preventDefault(); void signInWithPassword(); }}
    >
      <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-bold text-white shadow-lg">
          Z
        </span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Welcome back</p>
          <h1 className="text-xl font-bold text-white">Sign in to Zolexora TMS</h1>
        </div>
      </div>

      <button
        type="button"
        onClick={() => void signInWithGoogle()}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
      >
        Continue with Google
      </button>

      <div className="relative flex items-center justify-center">
        <div className="w-full border-t border-slate-800"></div>
        <span className="absolute bg-slate-900 px-3 text-xs text-slate-500 uppercase tracking-wider">
          or email
        </span>
      </div>

      <div className="flex flex-col gap-1.5 text-left">
        <label htmlFor="email" className="text-sm font-medium text-slate-300">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@company.com"
          autoComplete="email"
          required
          className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <PasswordField
        id="password"
        label="Password"
        name="password"
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
        placeholder="Enter your password"
      />

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
      >
        {isSubmitting ? "Signing in..." : "Sign In"}
      </button>

      {message && <p className="text-sm text-red-400" role="alert">{message}</p>}

      <div className="flex items-center justify-between border-t border-slate-800/80 pt-4 text-xs text-slate-400">
        <span>Need a workspace?</span>
        <Link to="/onboarding" className="font-semibold text-indigo-400 hover:text-indigo-300">
          Create Organisation
        </Link>
      </div>
    </form>
  );
}
