import { InputHTMLAttributes, useState } from "react";
import { Eye, EyeOff } from "lucide-react";


type PasswordInputProps = InputHTMLAttributes<HTMLInputElement>;


export function PasswordInput({ className = "", ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <input
        {...props}
        type={visible ? "text" : "password"}
        className={`w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-3 pr-12 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10 ${className}`}
      />
      <button
        type="button"
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute inset-y-0 right-2 grid w-10 place-items-center rounded-xl text-muted transition hover:bg-[#EDF0E8] hover:text-ink"
        onClick={() => setVisible((value) => !value)}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
}
