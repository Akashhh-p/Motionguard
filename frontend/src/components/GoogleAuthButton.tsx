import { Chrome } from "lucide-react";


export function GoogleAuthButton({ onClick, loading = false }: { onClick: () => void; loading?: boolean }) {
  return (
    <button
      type="button"
      disabled={loading}
      onClick={onClick}
      className="mt-4 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 text-sm font-semibold text-ink shadow-sm transition hover:-translate-y-0.5 hover:border-[#5E6B4F] hover:bg-[#EDF0E8] hover:shadow-premium disabled:cursor-not-allowed disabled:opacity-60"
    >
      <Chrome size={18} />
      {loading ? "Connecting..." : "Continue with Google"}
    </button>
  );
}
