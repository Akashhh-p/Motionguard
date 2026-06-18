import { Link } from "react-router-dom";
import { ArrowRight, Camera, FileText, ShieldCheck, Sparkles } from "lucide-react";

export function LandingPage() {
  return (
    <main className="min-h-screen bg-canvas">
      <section className="relative overflow-hidden border-b border-[#E5E7E1] bg-[radial-gradient(circle_at_18%_0%,rgba(94,107,79,0.13),transparent_34rem)]">
        <div className="mx-auto grid min-h-[86vh] max-w-7xl content-center gap-10 px-5 py-16 lg:grid-cols-[1.05fr_.95fr] lg:px-8">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#E5E7E1] bg-[#F7F8F4]/85 px-3 py-1 text-sm font-semibold text-brand shadow-sm backdrop-blur"><Sparkles size={16} /> AI video intelligence for real facilities</p>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-tight text-ink sm:text-5xl lg:text-6xl">MotionGuard AI Enterprise</h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-muted">A production-style surveillance analytics platform for teams that need uploaded video analysis, webcam monitoring, restricted zones, evidence, reports, and accountable multi-user data isolation.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/dashboard" className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-brand px-5 py-3 text-sm font-bold text-white shadow-premium transition hover:-translate-y-0.5 hover:bg-[#4F5B42]">Open Dashboard <ArrowRight size={18} /></Link>
              <Link to="/login" className="inline-flex min-h-11 items-center rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-5 py-3 text-sm font-bold text-ink transition hover:bg-[#EFF2EC]">Sign in</Link>
            </div>
          </div>
          <div className="grid content-end">
            <div className="rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF] p-4 shadow-premium">
              <div className="aspect-video rounded-[24px] bg-[#EFF2EC] p-4">
                <div className="h-full rounded-[20px] border border-[#E5E7E1] bg-[#F7F8F4] p-4">
                  <div className="mb-3 flex items-center justify-between text-sm font-semibold"><span>Camera Cluster 04</span><span className="text-teal">Live</span></div>
                  <div className="grid h-[78%] place-items-center rounded-lg border border-dashed border-[#E5E7E1] bg-[#EFF2EC] text-muted">Detection overlays, zones, and alerts render inside the console</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="mx-auto grid max-w-7xl gap-4 px-5 py-10 sm:grid-cols-2 lg:grid-cols-4 lg:px-8">
        {[
          ["Restricted zones", ShieldCheck],
          ["YOLOv8 detection", Camera],
          ["Evidence capture", FileText],
          ["Daily reports", Sparkles]
        ].map(([label, Icon]) => (
          <div key={String(label)} className="rounded-[22px] border border-[#E5E7E1] bg-[#FFFFFF] p-5 shadow-mist">
            <Icon className="mb-4 text-brand" size={24} />
            <h2 className="font-bold text-ink">{String(label)}</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Built into the operational workflow instead of isolated scripts.</p>
          </div>
        ))}
      </section>
    </main>
  );
}
