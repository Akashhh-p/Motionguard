import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { forgotPassword } from "../services/authService";
import { AuthShell } from "./LoginPage";


export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const data = await forgotPassword(email);
    setMessage(data.message);
  }

  return (
    <AuthShell title="Recover password" subtitle="Receive a secure reset link.">
      <form onSubmit={submit} className="space-y-4">
        <input className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-3 outline-none focus:border-brand" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Button className="w-full">Send reset link</Button>
      </form>
      {message && <p className="mt-4 rounded-2xl bg-[#EFF2EC] p-3 text-sm text-brand">{message}</p>}
      <p className="mt-5 text-center text-sm text-muted"><Link className="font-semibold text-brand" to="/login">Back to login</Link></p>
    </AuthShell>
  );
}
