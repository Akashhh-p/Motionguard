import { useEffect, useState } from "react";
import { Download, FilePlus, Trash2 } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../services/api";
import { formatLocalDateTime } from "../utils/time";

type Report = {
  id: number;
  report_date: string;
  summary: string;
  created_at: string;
};

type Toast = {
  type: "success" | "error";
  text: string;
} | null;

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [deleteTarget, setDeleteTarget] = useState<Report | null>(null);
  const [deleteConfirmTarget, setDeleteConfirmTarget] = useState<"bulk" | null>(null);
  const [toast, setToast] = useState<Toast>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = () => api.get("/reports").then((res) => setReports(res.data));

  useEffect(() => {
    load().catch(() => setToast({ type: "error", text: "Reports failed to load." }));
  }, []);

  async function generate() {
    setLoading(true);
    setToast(null);
    try {
      await api.post("/reports/generate", {});
      await load();
      setToast({ type: "success", text: "Report generated successfully." });
    } catch {
      setToast({ type: "error", text: "Report generation failed." });
    } finally {
      setLoading(false);
    }
  }

  async function download(id: number, format: "pdf" | "csv") {
    const res = await api.get(`/reports/${id}/download?format=${format}`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `motionguard-report.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    try {
      await api.delete(`/reports/${deleteTarget.id}`);
      setReports((items) => items.filter((item) => item.id !== deleteTarget.id));
      setToast({ type: "success", text: "Report deleted successfully." });
    } catch {
      setToast({ type: "error", text: "Report deletion failed." });
    } finally {
      setDeleteTarget(null);
    }
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function selectAll() {
    setSelectedIds(new Set(reports.map((report) => report.id)));
  }

  function deselectAll() {
    setSelectedIds(new Set());
  }

  async function confirmBulkDelete() {
    if (selectedIds.size === 0) return;
    setDeleteLoading(true);
    try {
      const response = await api.post("/reports/bulk-delete", {
        report_ids: Array.from(selectedIds),
      });
      
      setToast({
        type: "success",
        text: response.data.message || `${response.data.deleted_count} reports deleted.`,
      });
      
      setDeleteConfirmTarget(null);
      setReports((items) => items.filter((item) => !selectedIds.has(item.id)));
      setSelectedIds(new Set());
    } catch (error: any) {
      setToast({
        type: "error",
        text: error.response?.data?.detail || "Failed to delete reports.",
      });
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Reports</h1>
          <p className="text-sm text-muted">Daily PDF and CSV surveillance summaries generated from your data only.</p>
        </div>
        <Button disabled={loading} onClick={generate}><FilePlus size={18} /> {loading ? "Generating..." : "Generate Report"}</Button>
      </div>

      {toast && <div className={`rounded-2xl border p-3 text-sm font-semibold ${toast.type === "success" ? "border-[#D1FAE5] bg-[#ECFDF5] text-[#15803D]" : "border-[#FEE2E2] bg-[#FEF2F2] text-[#DC2626]"}`}>{toast.text}</div>}

      {selectedIds.size > 0 && (
        <div className="sticky bottom-0 left-0 right-0 z-40 flex items-center justify-between gap-4 rounded-2xl border border-[#5E6B4F] bg-[#EFF2EC] p-4 shadow-lg">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-ink">{selectedIds.size} selected</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={deselectAll}
              className="rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-2 text-sm font-semibold text-ink hover:bg-[#EFF2EC]"
            >
              Deselect All
            </button>
            <button
              onClick={() => setDeleteConfirmTarget("bulk")}
              className="inline-flex items-center gap-2 rounded-lg bg-[#DC2626] px-4 py-2 text-sm font-semibold text-white hover:bg-[#B91C1C]"
            >
              <Trash2 size={16} /> Delete Selected
            </button>
          </div>
        </div>
      )}

      {reports.length === 0 ? (
        <Card className="py-14 text-center">
          <h2 className="text-xl font-bold text-ink">No reports available</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-muted">Generate a report from real monitoring data.</p>
          <Button disabled={loading} onClick={generate} className="mx-auto mt-6"><FilePlus size={18} /> Generate Report</Button>
        </Card>
      ) : (
        <div>
          {reports.length > 0 && (
            <div className="mb-3 flex gap-2">
              <button
                onClick={selectAll}
                className="rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-1 text-xs font-semibold text-ink hover:bg-[#EFF2EC]"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-1 text-xs font-semibold text-ink hover:bg-[#EFF2EC]"
              >
                Clear Selection
              </button>
            </div>
          )}
          <div className="grid gap-4">
            {reports.map((report) => {
              const isSelectedItem = selectedIds.has(report.id);
              return (
                <Card
                  key={report.id}
                  className={
                    isSelectedItem
                      ? "border-[#5E6B4F] bg-[#F0F5ED]"
                      : undefined
                  }
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="font-bold text-ink">Daily report - {report.report_date}</p>
                      <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{report.summary}</p>
                      <p className="mt-2 text-xs text-muted">Generated {formatLocalDateTime(report.created_at)}</p>
                    </div>
                    <div className="flex gap-2">
                      <button className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white" onClick={() => download(report.id, "pdf")}><Download size={16} /> PDF</button>
                      <button className="inline-flex min-h-10 items-center rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-2 text-sm font-semibold text-ink" onClick={() => download(report.id, "csv")}>CSV</button>
                      <button className="grid size-10 place-items-center rounded-lg border border-[#FEE2E2] text-[#DC2626] hover:bg-[#FEF2F2]" onClick={() => setDeleteTarget(report)}><Trash2 size={16} /></button>
                      <input
                        type="checkbox"
                        checked={isSelectedItem}
                        onChange={() => toggleSelect(report.id)}
                        className="my-auto h-5 w-5 cursor-pointer rounded accent-[#5E6B4F]"
                      />
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#1F2937]/30 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF] p-6 shadow-premium">
            <h2 className="text-lg font-bold text-ink">Delete report?</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Are you sure you want to delete this report? This action cannot be undone.</p>
            <div className="mt-6 flex justify-end gap-2">
              <button className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-2 text-sm font-semibold text-ink hover:bg-[#EFF2EC]" onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="rounded-2xl bg-[#DC2626] px-4 py-2 text-sm font-semibold text-white hover:bg-[#B91C1C]" onClick={confirmDelete}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmTarget === "bulk" && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#1F2937]/30 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF] p-6 shadow-premium">
            <h2 className="text-lg font-bold text-ink">Delete selected reports?</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Are you sure you want to delete {selectedIds.size} selected report{selectedIds.size > 1 ? "s" : ""}? This action cannot be undone.</p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-2 text-sm font-semibold text-ink hover:bg-[#EFF2EC]"
                onClick={() => setDeleteConfirmTarget(null)}
                disabled={deleteLoading}
              >
                Cancel
              </button>
              <button
                className="inline-flex items-center gap-2 rounded-2xl bg-[#DC2626] px-4 py-2 text-sm font-semibold text-white hover:bg-[#B91C1C] disabled:opacity-50"
                onClick={confirmBulkDelete}
                disabled={deleteLoading}
              >
                {deleteLoading ? (
                  <>
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
