import { useEffect, useState } from "react";
import { Activity, Check, FileImage, FileText, ScanSearch, SquareDashedMousePointer } from "lucide-react";
import { api } from "../services/api";
import { Card } from "./Card";

type WorkflowKey = "live_motion" | "evidence_capture" | "object_analysis" | "zone_monitoring" | "report_ready";
type WorkflowStepStatus = "completed" | "active" | "idle";
type WorkflowStatus = Record<WorkflowKey, { status: WorkflowStepStatus; count: number }>;

const steps = [
  { key: "live_motion", label: "Live Motion", icon: Activity },
  { key: "evidence_capture", label: "Evidence Capture", icon: FileImage },
  { key: "object_analysis", label: "Object Analysis", icon: ScanSearch },
  { key: "zone_monitoring", label: "Zone Monitoring", icon: SquareDashedMousePointer },
  { key: "report_ready", label: "Report Ready", icon: FileText },
] as const;

export function AnimatedMonitoringWorkflow() {
  const [workflow, setWorkflow] = useState<WorkflowStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<WorkflowStatus>("/dashboard/workflow-status")
      .then((res) => setWorkflow(res.data))
      .catch(() => setError("Workflow status unavailable."));
  }, []);

  return (
    <Card className="overflow-hidden xl:col-span-1">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-bold text-ink">Animated Monitoring Workflow</h2>
          <p className="mt-1 text-sm text-muted">Real progress across MotionGuard activity stages.</p>
        </div>
        <div className="grid size-10 place-items-center rounded-2xl bg-[#EFF2EC] text-brand">
          <Activity size={20} />
        </div>
      </div>

      {error ? (
        <p className="mt-5 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-4 text-sm text-muted">{error}</p>
      ) : (
        <div className="workflow-flow mt-6">
          {steps.map(({ key, label, icon: Icon }, index) => {
            const item = workflow?.[key];
            const status = item?.status || "idle";
            const count = item?.count ?? 0;
            return (
              <div key={key} className="workflow-step" data-status={status}>
                {index < steps.length - 1 && <span className="workflow-connector" />}
                <div className="workflow-node">
                  <Icon size={18} className="workflow-icon" />
                  {status === "completed" && (
                    <span className="workflow-check">
                      <Check size={12} />
                    </span>
                  )}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-ink">{label}</p>
                  <p className="mt-1 text-xs text-muted">{count > 0 ? `${count} real record${count === 1 ? "" : "s"}` : "Not started"}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
