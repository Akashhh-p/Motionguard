import { ReactNode } from "react";
import clsx from "clsx";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={clsx("rounded-[22px] border border-[#E5E7E1] bg-[#FFFFFF] p-6 shadow-premium transition duration-300 hover:-translate-y-0.5 hover:shadow-glow", className)}>{children}</section>;
}
