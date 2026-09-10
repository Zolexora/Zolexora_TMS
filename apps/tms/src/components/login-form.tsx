"use client";

import Link from "next/link";
import { useState } from "react";
import { PasswordField } from "@/components/password-field";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <form className="auth-card" onSubmit={(event) => event.preventDefault()}>
      <div className="auth-header">
        <span className="brand-mark">Z</span>
        <div>
          <p className="eyebrow neutral">Welcome back</p>
          <h1>Sign in to Zolexora</h1>
        </div>
      </div>

      <button type="button" className="social-button">
        Continue with Google
      </button>

      <div className="divider">
        <span>or continue with email</span>
      </div>

      <div className="field-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@company.com"
          autoComplete="email"
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

      <div className="form-row justify-between">
        <label className="remember-me">
          <input type="checkbox" />
          <span>Remember me</span>
        </label>
        <Link href="/login" className="tiny-link">
          Forgot Password?
        </Link>
      </div>

      <button type="submit" className="primary-button full-width">
        Sign In
      </button>

      <div className="auth-links">
        <span>Need a workspace?</span>
        <Link href="/onboarding">Create Organisation</Link>
      </div>
    </form>
  );
}
