import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Activity, Aperture, RadioTower } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/Button";
import { PasswordInput } from "../components/PasswordInput";
import { GoogleAuthButton } from "../components/GoogleAuthButton";

export function LoginPage() {
  const { login, continueWithGoogle, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) navigate("/dashboard");
  }, [user, navigate]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (exc: any) {
      setError(exc.response?.data?.detail || exc.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Sign in" subtitle="Access your isolated MotionGuard workspace.">
      <form onSubmit={submit} className="space-y-4">
        <input className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-3 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <PasswordInput placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="rounded-2xl bg-[#FEF2F2] px-3 py-2 text-sm text-[#DC2626]">{error}</p>}
        <Button disabled={loading} className="w-full">{loading ? "Signing in..." : "Login"}</Button>
      </form>
      <GoogleAuthButton onClick={() => continueWithGoogle().then(() => navigate("/dashboard")).catch((exc) => setError(exc.message || "Google sign-in failed."))} loading={loading} />
      <p className="mt-5 text-center text-sm text-muted"><Link className="font-semibold text-brand" to="/forgot-password">Forgot password?</Link></p>
      <p className="mt-2 text-center text-sm text-muted">No account? <Link className="font-semibold text-brand" to="/signup">Create one</Link></p>
    </AuthShell>
  );
}

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-canvas px-4 py-10">
      <div className="absolute left-[8%] top-[9%] h-28 w-28 rounded-[32px] border border-[#E5E7E1] bg-[#F7F8F4]/70 shadow-premium auth-orbit" />
      <div className="absolute bottom-[13%] right-[9%] h-36 w-36 rounded-full border border-[#D8D5C8] bg-[#8A735A]/10 auth-orbit" />
      <div className="absolute inset-x-0 top-24 h-24 bg-[linear-gradient(90deg,transparent,rgba(94,107,79,0.10),transparent)] blur-3xl auth-wave" />
      <section className="relative mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[1.08fr_.92fr]">
        <div className="hidden lg:block">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#E5E7E1] bg-[#F7F8F4]/80 px-3 py-1 text-sm font-semibold text-[#5E6B4F] shadow-premium backdrop-blur">
            <RadioTower size={16} /> Enterprise surveillance intelligence
          </div>
          <h1 className="max-w-2xl text-5xl font-extrabold leading-tight text-ink">MotionGuard AI Enterprise</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-muted">A calm command surface for motion events, object intelligence, zone monitoring, evidence review, and operational reporting.</p>
          <div className="mt-10 rounded-[24px] border border-[#E5E7E1] bg-[#F7F8F4]/78 p-5 shadow-premium backdrop-blur">
            <svg viewBox="0 0 520 300" className="h-auto w-full" role="img" aria-label="Surveillance intelligence visualization">
              <defs>
                <linearGradient id="sage-auth" x1="0" x2="1">
                  <stop offset="0" stopColor="#5E6B4F" stopOpacity=".92" />
                  <stop offset="1" stopColor="#8A735A" stopOpacity=".78" />
                </linearGradient>
              </defs>
              <rect x="18" y="20" width="484" height="260" rx="28" fill="#FFFFFF" stroke="#E5E7E1" />
              <path d="M58 214 C132 152, 188 236, 268 166 S392 76, 462 122" fill="none" stroke="#8A735A" strokeWidth="4" strokeLinecap="round" className="auth-wave" />
              <circle cx="152" cy="132" r="52" fill="#EFF2EC" stroke="#E5E7E1" />
              <path d="M117 136 C139 106, 169 106, 190 136 C169 166, 139 166, 117 136Z" fill="none" stroke="#5E6B4F" strokeWidth="5" />
              <circle cx="154" cy="136" r="13" fill="#5E6B4F" />
              <rect x="292" y="84" width="134" height="28" rx="14" fill="#E7EBE2" />
              <rect x="292" y="128" width="174" height="28" rx="14" fill="#F0E9DF" />
              <rect x="292" y="172" width="108" height="28" rx="14" fill="#E5F0E7" />
              <circle cx="74" cy="68" r="10" fill="#15803D" />
              <circle cx="446" cy="230" r="12" fill="#B45309" />
            </svg>
          </div>
        </div>
        <section className="w-full rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF]/94 p-7 shadow-premium backdrop-blur-xl">
          <div className="mb-6">
            <div className="mb-4 flex items-center gap-2 text-[#5E6B4F]">
              <Aperture size={22} />
              <span className="text-sm font-bold uppercase tracking-[0.18em]">MotionGuard</span>
            </div>
            <h1 className="text-2xl font-bold text-ink">{title}</h1>
            <p className="mt-1 text-sm text-muted">{subtitle}</p>
          </div>
          {children}
          <div className="mt-6 flex items-center gap-2 text-xs font-semibold text-muted">
            <Activity size={14} className="text-[#15803D]" /> Encrypted workspace session
          </div>
        </section>
      </section>
    </main>
  );
}
