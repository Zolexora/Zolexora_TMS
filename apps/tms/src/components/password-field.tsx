"use client";

import { useState } from "react";

export function PasswordField({
  id,
  label,
  value,
  onChange,
  name,
  autoComplete,
  placeholder,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  name?: string;
  autoComplete?: string;
  placeholder?: string;
}) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="field-group field-password">
      <label htmlFor={id}>{label}</label>
      <div className="input-wrap password-wrap">
        <input
          id={id}
          type={showPassword ? "text" : "password"}
          name={name}
          value={value}
          autoComplete={autoComplete}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          type="button"
          className="password-toggle"
          aria-label={showPassword ? "Hide password" : "Show password"}
          onClick={() => setShowPassword((current) => !current)}
        >
          {showPassword ? "Hide" : "Show"}
        </button>
      </div>
    </div>
  );
}
