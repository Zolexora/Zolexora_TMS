import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PasswordField } from "./password-field";
import { supabase } from "../lib/supabase";
import { useAuth } from "../features/auth/useAuth";

const organisationTypes = [
  "Sole Proprietorship / Proprietor",
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
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  // const navigate = useNavigate();

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

  const { session } = useAuth();
  const [otp, setOtp] = useState("");
  const [showOtpInput, setShowOtpInput] = useState(false);

  async function createAccount() {
    setIsSubmitting(true);
    setMessage("");

    let currentSession = session;

    if (!currentSession) {
      // Step A: Not authenticated yet. Sign up with Supabase.
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            organisation_name: organisationName,
            organisation_type: organisationType,
          },
        },
      });

      if (error) {
        setIsSubmitting(false);
        setMessage(`Unable to create account: ${error.message}`);
        return;
      }

      if (data.session) {
        currentSession = data.session;
      } else {
        // Require OTP verification
        setIsSubmitting(false);
        setShowOtpInput(true);
        setMessage("A verification code has been sent to your email.");
        return;
      }
    }

    await completeBackendOnboarding(currentSession);
  }

  async function verifyOtpAndComplete() {
    setIsSubmitting(true);
    setMessage("");
    const { data, error } = await supabase.auth.verifyOtp({
      email,
      token: otp,
      type: 'signup'
    });

    if (error || !data.session) {
      setIsSubmitting(false);
      setMessage(error?.message || "Invalid or expired OTP code.");
      return;
    }

    await completeBackendOnboarding(data.session);
  }

  async function completeBackendOnboarding(activeSession: any) {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/onboarding`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${activeSession.access_token}`,
          },
          body: JSON.stringify({
            name: organisationName,
            organisation_type: organisationType,
          }),
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create organisation');
      }

      setMessage("Organisation created successfully! Entering Command Center...");
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);
    } catch (err: any) {
      setMessage(err.message);
      setIsSubmitting(false);
    }
  }

  return (
    <form 
      className="mx-auto flex w-full max-w-lg flex-col gap-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl"
      onSubmit={(event) => { event.preventDefault(); void createAccount(); }}
    >
      <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-bold text-white shadow-lg">
          Z
        </span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Step {step} of 2</p>
          <h1 className="text-xl font-bold text-white">Create Organisation & Commander</h1>
        </div>
      </div>

      <div className="flex gap-2">
        <div className={`h-1 flex-1 rounded-full ${step >= 1 ? 'bg-indigo-500' : 'bg-slate-800'}`} />
        <div className={`h-1 flex-1 rounded-full ${step >= 2 ? 'bg-indigo-500' : 'bg-slate-800'}`} />
      </div>

      {step === 1 ? (
        <>
          <div className="flex flex-col gap-1.5 text-left">
            <label htmlFor="organisation-name" className="text-sm font-medium text-slate-300">
              Organisation Name
            </label>
            <input
              id="organisation-name"
              value={organisationName}
              onChange={(event) => setOrganisationName(event.target.value)}
              placeholder="e.g. Apex Logistics India"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex flex-col gap-1.5 text-left">
            <label htmlFor="organisation-type" className="text-sm font-medium text-slate-300">
              Organisation Type
            </label>
            <select
              id="organisation-type"
              value={organisationType}
              onChange={(event) => setOrganisationType(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {organisationTypes.map((type) => (
                <option key={type} value={type} className="bg-slate-900 text-white">
                  {type}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            disabled={!isStepOneValid}
            onClick={() => {
              if (session) {
                void createAccount();
              } else {
                setStep(2);
              }
            }}
            className="mt-2 w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {session ? (isSubmitting ? "Creating..." : "Create Workspace") : "Next: Commander Details"}
          </button>
        </>
      ) : (
        <>
          <div className="flex flex-col gap-1.5 text-left">
            <label htmlFor="full-name" className="text-sm font-medium text-slate-300">
              Commander Full Name
            </label>
            <input
              id="full-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="e.g. Rajesh Sharma"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5 text-left">
              <label htmlFor="email" className="text-sm font-medium text-slate-300">
                Commander Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="commander@apex.com"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div className="flex flex-col gap-1.5 text-left">
              <label htmlFor="confirm-email" className="text-sm font-medium text-slate-300">
                Confirm Email
              </label>
              <input
                id="confirm-email"
                type="email"
                value={confirmEmail}
                onChange={(event) => setConfirmEmail(event.target.value)}
                placeholder="Re-enter email"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <PasswordField
            id="create-password"
            label="Password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            placeholder="Min 8 chars, uppercase, number & symbol"
          />

          <PasswordField
            id="confirm-password"
            label="Confirm Password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            autoComplete="new-password"
            placeholder="Re-enter password"
          />

          {showOtpInput ? (
            <div className="flex flex-col gap-3 pt-2">
              <label htmlFor="otp" className="text-sm font-medium text-slate-300">
                Enter 6-digit Verification Code
              </label>
              <input
                id="otp"
                type="text"
                maxLength={6}
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="w-full text-center tracking-widest text-xl rounded-lg border border-slate-700 bg-slate-900/80 px-3.5 py-3 font-mono text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => void verifyOtpAndComplete()}
                disabled={otp.length < 6 || isSubmitting}
                className="w-full mt-2 rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isSubmitting ? "Verifying..." : "Verify & Create Workspace"}
              </button>
            </div>
          ) : (
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-1/3 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-slate-700"
              >
                Back
              </button>
              <button
                type="button"
                disabled={!isStepTwoValid || isSubmitting}
                onClick={() => {
                  if (session) {
                    void createAccount();
                  } else {
                    void createAccount();
                  }
                }}
                className="w-2/3 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isSubmitting ? "Creating..." : "Create Workspace"}
              </button>
            </div>
          )}
        </>
      )}

      {message && <p className="text-sm text-amber-400" role="status">{message}</p>}

      <div className="flex items-center justify-between border-t border-slate-800/80 pt-4 text-xs text-slate-400">
        <span>Already have an organisation?</span>
        <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300">
          Sign In
        </Link>
      </div>
    </form>
  );
}
