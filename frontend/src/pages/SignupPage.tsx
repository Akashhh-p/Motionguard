import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { useAuth } from "../context/AuthContext";
import { AuthShell } from "./LoginPage";
import { PasswordInput } from "../components/PasswordInput";
import { GoogleAuthButton } from "../components/GoogleAuthButton";

export function SignupPage() {
  const { signup, continueWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (!/[A-Z]/.test(password) || !/\d/.test(password) || password.length < 8) {
      setError("Password must be 8+ characters with an uppercase letter and a number.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await signup(fullName.trim(), email.trim(), password);
      navigate("/dashboard");
    } catch (exc: any) {
      const detail = exc.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((item: any) => item.msg).join(" ") : detail || exc.message || "Signup failed. Try a different email or check the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Create account" subtitle="Start with an empty, private workspace.">
      <form onSubmit={submit} className="space-y-4">
        <input className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-3 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10" placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        <input className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-3 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <PasswordInput placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <PasswordInput placeholder="Confirm password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        {error && <p className="rounded-2xl bg-[#FEF2F2] px-3 py-2 text-sm text-[#DC2626]">{error}</p>}
        <Button disabled={loading} className="w-full">{loading ? "Creating..." : "Signup"}</Button>
      </form>
      <GoogleAuthButton onClick={() => continueWithGoogle().then(() => navigate("/dashboard")).catch((exc) => setError(exc.message || "Google sign-in failed."))} loading={loading} />
      <p className="mt-5 text-center text-sm text-muted">Already registered? <Link className="font-semibold text-brand" to="/login">Login</Link></p>
    </AuthShell>
  );
}
