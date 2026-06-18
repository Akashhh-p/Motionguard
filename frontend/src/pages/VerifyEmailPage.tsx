import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../services/authService";
import { AuthShell } from "./LoginPage";


export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    verifyEmail(params.get("oobCode") || params.get("token") || "")
      .then((data) => setMessage(data.message))
      .catch((exc) => setMessage(exc.response?.data?.detail || "Verification failed."));
  }, [params]);

  return (
    <AuthShell title="Email verification" subtitle="Activate your MotionGuard account.">
      <p className="rounded-2xl bg-[#EFF2EC] p-3 text-sm text-brand">{message}</p>
      <p className="mt-5 text-center text-sm text-muted"><Link className="font-semibold text-brand" to="/login">Go to login</Link></p>
    </AuthShell>
  );
}
