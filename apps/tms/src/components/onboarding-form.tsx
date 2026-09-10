"use client";

import { useMemo, useState } from "react";
import { PasswordField } from "@/components/password-field";

const organisationTypes = [
  "Proprietorship / Sole Proprietorship",
  "Partnership Firm",
  "Limited Liability Partnership (LLP)",
  "Private Limited Company",
  "Public Limited Company",
  "One Person Company (OPC)",
  "Limited Company",
  "Section 8 Company",
  "Non-Profit Organisation",
  "Trust",
  "Public Trust",
  "Private Trust",
  "Charitable Trust",
  "Society",
  "Co-operative Society",
  "Hindu Undivided Family (HUF)",
  "Government Organisation",
  "Government Department",
  "Public Sector Undertaking (PSU)",
  "Municipal Corporation",
  "Local Government Body",
  "Educational Institution",
  "University",
  "School",
  "College",
  "Hospital",
  "Healthcare Organisation",
  "NGO",
  "Religious Organisation",
  "Foundation",
  "Family Office",
  "Startup",
  "Freelancer / Individual",
  "Self Employed",
  "Other",
];

export function OnboardingForm() {
  const [step, setStep] = useState(1);
  const [organisationName, setOrganisationName] = useState("");
  const [organisationType, setOrganisationType] = useState(organisationTypes[0]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [confirmEmail, setConfirmEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const passwordValid = useMemo(() => {
    if (password.length < 8) return false;
    return /[A-Z]/.test(password) && /[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password);
  }, [password]);

  const isStepOneValid = organisationName.trim().length > 1 && organisationType.trim().length > 0;
  const isStepTwoValid =
    fullName.trim().length > 1 &&
    email.trim().length > 0 &&
    email === confirmEmail &&
    passwordValid &&
    password === confirmPassword;

  return (
    <form className="auth-card onboarding-card" onSubmit={(event) => event.preventDefault()}>
      <div className="auth-header">
        <div className="brand-mark">Z</div>
        <div>
          <p className="eyebrow neutral">Create your organisation</p>
          <h1>Set up your Zolexora workspace</h1>
        </div>
      </div>

      <div className="stepper" aria-label="Onboarding progress">
        <span className={step === 1 ? "active" : ""}>1</span>
        <span className={step === 2 ? "active" : ""}>2</span>
      </div>

      {step === 1 ? (
        <>
          <div className="field-group">
            <label htmlFor="organisation-name">Organisation Name</label>
            <input
              id="organisation-name"
              value={organisationName}
              onChange={(event) => setOrganisationName(event.target.value)}
              placeholder="e.g. BluePeak Logistics"
            />
          </div>

          <div className="field-group">
            <label htmlFor="organisation-type">Organisation Type</label>
            <select
              id="organisation-type"
              value={organisationType}
              onChange={(event) => setOrganisationType(event.target.value)}
            >
              {organisationTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="primary-button full-width"
            disabled={!isStepOneValid}
            onClick={() => setStep(2)}
          >
            Next
          </button>
        </>
      ) : (
        <>
          <div className="field-group">
            <label htmlFor="full-name">Full Name</label>
            <input
              id="full-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Enter your full name"
            />
          </div>

          <div className="field-group">
            <label htmlFor="email-step">Email</label>
            <input
              id="email-step"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="commander@company.com"
            />
          </div>

          <div className="field-group">
            <label htmlFor="confirm-email">Verify Email</label>
            <input
              id="confirm-email"
              type="email"
              value={confirmEmail}
              onChange={(event) => setConfirmEmail(event.target.value)}
              placeholder="Re-enter email"
            />
          </div>

          <PasswordField
            id="create-password"
            label="Password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            placeholder="Create a strong password"
          />
          {!password ? null : passwordValid ? (
            <p className="assistive success">Strong password accepted.</p>
          ) : (
            <p className="assistive warning">Use 8+ characters, a capital letter, a number, and a symbol.</p>
          )}

          <PasswordField
            id="confirm-password"
            label="Re-enter Password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            autoComplete="new-password"
            placeholder="Confirm password"
          />
          {!confirmPassword ? null : password === confirmPassword ? (
            <p className="assistive success">Passwords match.</p>
          ) : (
            <p className="assistive warning">Passwords do not match.</p>
          )}

          <div className="form-row">
            <button type="button" className="secondary-button" onClick={() => setStep(1)}>
              Back
            </button>
            <button type="submit" className="primary-button" disabled={!isStepTwoValid}>
              Create Workspace
            </button>
          </div>
        </>
      )}
    </form>
  );
}
