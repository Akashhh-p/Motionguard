import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../components/Button";
import { PasswordInput } from "../components/PasswordInput";
import { resetPassword } from "../services/authService";
import { AuthShell } from "./LoginPage";


export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    try {
      await resetPassword(params.get("oobCode") || params.get("token") || "", password);
      navigate("/login");
    } catch (exc: any) {
      setError(exc.response?.data?.detail || "Reset failed.");
    }
  }

  return (
    <AuthShell title="Reset password" subtitle="Choose a new secure password.">
      <form onSubmit={submit} className="space-y-4">
        <PasswordInput placeholder="New password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <PasswordInput placeholder="Confirm password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        {error && <p className="rounded-2xl bg-[#FEF2F2] p-3 text-sm text-[#DC2626]">{error}</p>}
        <Button className="w-full">Reset password</Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted"><Link className="font-semibold text-brand" to="/login">Back to login</Link></p>
    </AuthShell>
  );
}
