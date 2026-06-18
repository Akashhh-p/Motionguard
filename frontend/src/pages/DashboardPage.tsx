import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Camera, Clock, Database, FileImage, LockKeyhole, ScanSearch, ShieldCheck, SquareDashedMousePointer } from "lucide-react";
import { AnimatedMonitoringWorkflow } from "../components/AnimatedMonitoringWorkflow";
import { Card } from "../components/Card";
import { api } from "../services/api";
import { formatLocalDateTime, formatRelativeTime, formatTimelineTime } from "../utils/time";

type MotionActivity = {
  id: number;
  event_type: string;
  source_type: string;
  motion_count: number;
  estimated_moving_subjects: number;
  motion_area_total: number;
  timestamp: string;
};

type EvidenceActivity = {
  id: number;
  object_class?: string | null;
  evidence_type: string;
  created_at: string;
};

type ZoneActivity = {
  id: number;
  name: string;
  zone_type: string;
  source_type: string;
  created_at: string;
};

type DashboardSummary = {
  motion_events_today: number;
  evidence_items: number;
  active_zones: number;
  zone_violations: number;
  last_motion_time: string | null;
  latest_motion_count: number;
  latest_motion_source: string | null;
  recent_motion_events: MotionActivity[];
  recent_evidence: EvidenceActivity[];
  active_zone_items: ZoneActivity[];
  recent_zone_events: { id: number; event_type: string; zone_id: number; motion_count: number; object_count: number; timestamp: string }[];
  activity_timeline: { id: string; label: string; timestamp: string; source: string }[];
};

type HealthStatus = {
  database: string;
  auth: string;
  motion_engine: string;
  evidence_engine: string;
  zone_engine: string;
};

const emptySummary: DashboardSummary = {
  motion_events_today: 0,
  evidence_items: 0,
  active_zones: 0,
  zone_violations: 0,
  last_motion_time: null,
  latest_motion_count: 0,
  latest_motion_source: null,
  recent_motion_events: [],
  recent_evidence: [],
  active_zone_items: [],
  recent_zone_events: [],
  activity_timeline: [],
};

const unavailableHealth: HealthStatus = {
  database: "unavailable",
  auth: "unavailable",
  motion_engine: "unavailable",
  evidence_engine: "unavailable",
  zone_engine: "unavailable",
};

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [health, setHealth] = useState<HealthStatus>(unavailableHealth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [, setRelativeTick] = useState(0);

  useEffect(() => {
    Promise.allSettled([api.get("/dashboard/summary"), api.get("/system/health")])
      .then(([summaryResult, healthResult]) => {
        if (summaryResult.status === "fulfilled") setSummary({ ...emptySummary, ...summaryResult.value.data });
        else setError("Dashboard data failed to load.");
        if (healthResult.status === "fulfilled") setHealth({ ...unavailableHealth, ...healthResult.value.data });
        else setHealth(unavailableHealth);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setRelativeTick((value) => value + 1), 30000);
    return () => window.clearInterval(timer);
  }, []);

  const hasActivity = summary.motion_events_today > 0 || summary.evidence_items > 0 || summary.active_zones > 0 || Boolean(summary.last_motion_time);
  const kpis = [
    ["Motion Events Today", summary.motion_events_today, Activity],
    ["Evidence Items", summary.evidence_items, FileImage],
    ["Active Zones", summary.active_zones, SquareDashedMousePointer],
    ["Last Motion Detected", summary.last_motion_time ? formatLocalDateTime(summary.last_motion_time) : "No motion yet", Clock],
  ] as const;

  if (loading) {
    return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 5 }).map((_, index) => <Card key={index} className="h-32 animate-pulse bg-[#F7F8F4]"><span /></Card>)}</div>;
  }

  if (error) {
    return <Card><p className="text-sm font-semibold text-[#DC2626]">{error}</p></Card>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Dashboard</h1>
        <p className="text-sm text-muted">Real user-scoped motion, evidence, zone, and system activity.</p>
      </div>

      <IntelligenceHero />
      <StatusStrip health={health} />

      {!hasActivity && <EmptyWorkspace />}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {kpis.map(([label, value, Icon]) => (
          <Card key={label} className="min-h-32">
            <div className="flex h-full items-center justify-between">
              <div>
                <p className="text-sm text-muted">{label}</p>
                <p className="mt-2 text-2xl font-bold text-ink">{value}</p>
              </div>
              <div className="grid size-11 place-items-center rounded-2xl bg-[#EFF2EC] text-brand"><Icon size={22} /></div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[.9fr_1.1fr]">
        <AnimatedMonitoringWorkflow />
        <QuickActions />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ActivityList title="Recent Motion Events" empty="No motion recorded yet." items={summary.recent_motion_events.map((item) => ({
          id: item.id,
          title: `${item.event_type || "Motion"} from ${item.source_type || "unknown source"}`,
          meta: formatLocalDateTime(item.timestamp),
          value: `${item.motion_count || 0} boxes`,
        }))} />
        <ActivityList title="Recent Evidence" empty="No evidence captured yet." items={summary.recent_evidence.map((item) => ({
          id: item.id,
          title: `Evidence #${item.id}`,
          meta: `${item.evidence_type} - ${formatLocalDateTime(item.created_at)}`,
          value: item.object_class || "Not analyzed",
        }))} />
        <ActivityList title="Active Zones" empty="No zones configured yet." items={summary.active_zone_items.map((item) => ({
          id: item.id,
          title: item.name,
          meta: `${item.zone_type} - ${item.source_type}`,
          value: "Active",
          tone: "ok",
        }))} />
        <ActivityList title="Recent Activity Timeline" empty="No activity recorded yet." items={summary.activity_timeline.map((item, index) => ({
          id: index,
          title: item.label,
          meta: formatTimelineTime(item.timestamp),
          value: `${formatRelativeTime(item.timestamp)} - ${item.source}`,
        }))} />
      </div>
    </div>
  );
}

function IntelligenceHero() {
  return (
    <section className="relative overflow-hidden rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF] p-6 shadow-premium">
      <div className="absolute inset-0 surveillance-grid opacity-70" />
      <div className="absolute right-8 top-1/2 hidden h-36 w-52 -translate-y-1/2 rounded-[24px] border border-[#E5E7E1] bg-[#F7F8F4]/80 p-5 shadow-sm backdrop-blur md:block">
        <div className="space-y-3">
          <div className="h-2 rounded-full bg-[#E7EBE2]" />
          <div className="h-2 w-4/5 rounded-full bg-[#EFE7DB]" />
          <div className="h-2 w-2/3 rounded-full bg-[#E5E7E1]" />
        </div>
        <div className="absolute bottom-5 left-5 right-5 flex items-center justify-between">
          <span className="size-2 rounded-full bg-[#15803D]" />
          <span className="h-px flex-1 bg-[#DDE3EA]" />
          <span className="size-2 rounded-full bg-[#8A735A]" />
        </div>
      </div>
      <div className="relative max-w-2xl">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-[#5E6B4F]">
          <Activity size={15} /> Intelligence online
        </div>
        <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">MotionGuard Intelligence Active</h2>
        <p className="mt-3 text-sm leading-6 text-muted sm:text-base">Monitoring motion, zones, and evidence from real system activity.</p>
        <div className="motion-wave mt-6 h-1.5 w-full max-w-md rounded-full bg-[#EFF2EC]" />
      </div>
      <div className="scan-line absolute inset-x-0 top-0 h-px bg-[#5E6B4F]/40" />
    </section>
  );
}

function StatusStrip({ health }: { health: HealthStatus }) {
  const chips = [
    ["Database Connected", health.database, Database],
    ["Auth Secured", health.auth, LockKeyhole],
    ["Motion Engine Ready", health.motion_engine, Activity],
    ["Evidence Engine Ready", health.evidence_engine, FileImage],
    ["Zone Monitor Ready", health.zone_engine, ShieldCheck],
  ] as const;

  return (
    <div className="grid gap-3 md:grid-cols-5">
      {chips.map(([label, status, Icon]) => {
        const ok = ["connected", "active", "ready"].includes(String(status).toLowerCase());
        return (
          <div key={label} className="flex min-h-16 items-center gap-3 rounded-[20px] border border-[#E5E7E1] bg-[#F7F8F4] px-4 shadow-premium">
            <span className={`status-pip ${ok ? "bg-[#15803D]" : "bg-[#B45309]"}`} />
            <Icon size={17} className={ok ? "text-[#15803D]" : "text-[#B45309]"} />
            <div>
              <p className="text-xs font-bold text-ink">{label}</p>
              <p className="text-xs capitalize text-muted">{status || "unavailable"}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function QuickActions() {
  const actions = [
    ["/live-monitoring", "Start Live Monitoring", "Open real-time motion detection.", Camera],
    ["/evidence", "Analyze Evidence", "Upload or inspect captured evidence.", ScanSearch],
    ["/zones", "Configure Zones", "Define monitored spaces.", SquareDashedMousePointer],
    ["/reports", "Open Reports", "Generate event-based summaries.", ShieldCheck],
  ] as const;

  return (
    <Card>
      <h2 className="font-bold text-ink">Quick Actions</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {actions.map(([to, title, subtitle, Icon]) => (
          <Link key={to} to={to} className="group rounded-[20px] border border-[#E5E7E1] bg-gradient-to-br from-[#FFFFFF] to-[#F7F8F4] p-4 shadow-sm transition duration-300 hover:-translate-y-1 hover:border-[#5E6B4F]/50 hover:shadow-glow">
            <div className="flex items-start justify-between gap-3">
              <div className="grid size-10 place-items-center rounded-2xl bg-[#EFF2EC] text-brand transition group-hover:bg-[#E7EBE2]"><Icon size={19} /></div>
              <ArrowRight size={17} className="text-muted transition group-hover:translate-x-1 group-hover:text-brand" />
            </div>
            <p className="mt-4 font-bold text-ink">{title}</p>
            <p className="mt-1 text-sm leading-5 text-muted">{subtitle}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function EmptyWorkspace() {
  return (
    <Card className="relative overflow-hidden">
      <div className="absolute right-8 top-6 hidden h-20 w-28 rounded-[20px] border border-[#5E6B4F]/20 bg-[#F7F8F4] md:block">
        <div className="absolute left-4 right-4 top-6 h-px bg-[#5E6B4F]/20" />
        <div className="absolute left-4 right-8 top-11 h-px bg-[#8A735A]/20" />
        <span className="absolute bottom-4 right-4 size-2 rounded-full bg-[#5E6B4F]" />
      </div>
      <div className="relative max-w-xl">
        <h2 className="text-xl font-bold text-ink">Your intelligence workspace is ready.</h2>
        <p className="mt-2 text-sm leading-6 text-muted">Start live monitoring or analyze evidence to begin collecting real activity data.</p>
      </div>
    </Card>
  );
}

function ActivityList({ title, empty, items }: { title: string; empty: string; items: { id: number; title: string; meta: string; value: string | number; tone?: "ok" | "danger" }[] }) {
  return (
    <Card>
      <h2 className="mb-4 font-bold text-ink">{title}</h2>
      {items.length === 0 ? <p className="text-sm text-muted">{empty}</p> : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2">
              <div>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="text-xs text-muted">{item.meta}</p>
              </div>
              <span className={`shrink-0 rounded-full px-2 py-1 text-xs font-bold ${item.tone === "danger" ? "bg-[#FEF2F2] text-[#DC2626]" : item.tone === "ok" ? "bg-[#ECFDF5] text-[#15803D]" : "bg-[#EFF2EC] text-ink"}`}>{item.value}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
