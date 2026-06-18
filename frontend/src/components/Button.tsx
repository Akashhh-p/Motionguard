import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl bg-[#5E6B4F] px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-[#1F2937]/10 transition duration-200 hover:-translate-y-0.5 hover:bg-[#4F5B42] hover:shadow-glow disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0",
        className
      )}
      {...props}
    />
  );
}
