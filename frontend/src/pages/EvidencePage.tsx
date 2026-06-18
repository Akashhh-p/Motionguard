import { ChangeEvent, useEffect, useRef, useState } from "react";
import { Camera, Download, Pause, ScanSearch, Trash2, Upload, Check, X } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../services/api";
import { formatLocalDateTime } from "../utils/time";


type EvidenceItem = {
  id: number;
  object_class?: string | null;
  evidence_type: string;
  created_at: string;
};

type ObjectDetection = {
  class_name: string;
  confidence: number;
  bbox: number[];
};

type EvidenceAnalysisResult = {
  evidence_id: number;
  detections: ObjectDetection[];
  frame_width: number;
  frame_height: number;
};

type LiveObjectResult = {
  success?: boolean;
  detections: ObjectDetection[];
  human_count: number;
  object_count: number;
  fps: number;
  frame_width: number;
  frame_height: number;
  debug?: {
    model_loaded?: boolean;
    input_shape?: number[];
    detections_count?: number;
    inference_ms?: number;
    confidence?: number;
  };
};

type Toast = {
  type: "success" | "error";
  text: string;
} | null;


export function EvidencePage() {
  const [items, setItems] = useState<EvidenceItem[]>([]);
  const [objectClass, setObjectClass] = useState("");
  const [selected, setSelected] = useState<EvidenceItem | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [upload, setUpload] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [analysis, setAnalysis] = useState<EvidenceAnalysisResult | null>(null);
  const [message, setMessage] = useState("");
  const imageRef = useRef<HTMLImageElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const captureRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const busyRef = useRef(false);
  const [liveRunning, setLiveRunning] = useState(false);
  const [liveResult, setLiveResult] = useState<LiveObjectResult | null>(null);
  const [debugMode, setDebugMode] = useState(false);
  const [confidence, setConfidence] = useState(0.25);
  const [frameSentCount, setFrameSentCount] = useState(0);
  const [lastResponseMs, setLastResponseMs] = useState(0);
  const [lastError, setLastError] = useState("");
  const [backendConnected, setBackendConnected] = useState(false);
  const [deleteConfirmTarget, setDeleteConfirmTarget] = useState<"bulk" | null>(null);
  const [toast, setToast] = useState<Toast>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = () => api.get("/evidence", { params: { object_class: objectClass || undefined } }).then((res) => setItems(res.data));

  useEffect(() => { load(); }, []);
  useEffect(() => { drawDetections(); }, [analysis, liveResult, previewUrl]);
  useEffect(() => () => stopLiveObjectDetection(), []);

  function clearPreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl("");
  }

  async function download(id: number) {
    try {
      const res = await api.get(`/files/evidence/${id}/download`, { responseType: "blob" });
      if (res.data && res.data.size > 0) {
        const url = URL.createObjectURL(res.data);
        window.open(url, "_blank");
      } else {
        setMessage("Failed to download evidence - file is empty.");
      }
    } catch (error) {
      setMessage("Failed to download evidence.");
      console.error("Error downloading evidence:", error);
    }
  }

  async function remove(id: number) {
    try {
      await api.delete(`/evidence/${id}`);
      if (selected?.id === id) {
        setSelected(null);
        setAnalysis(null);
        clearPreview();
      }
      setToast({ type: "success", text: "Evidence deleted successfully." });
      await load();
    } catch {
      setToast({ type: "error", text: "Failed to delete evidence." });
    }
  }

  function toggleSelect(id: number, event?: React.MouseEvent) {
    if (event) event.stopPropagation();
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
    setSelectedIds(new Set(items.map((item) => item.id)));
  }

  function deselectAll() {
    setSelectedIds(new Set());
  }

  async function confirmBulkDelete() {
    if (selectedIds.size === 0) return;
    setDeleteLoading(true);
    try {
      const response = await api.post("/evidence/bulk-delete", {
        evidence_ids: Array.from(selectedIds),
      });
      
      setToast({
        type: "success",
        text: response.data.message || `${response.data.deleted_count} evidence items deleted.`,
      });
      
      setDeleteConfirmTarget(null);
      setSelectedIds(new Set());
      if (selected && selectedIds.has(selected.id)) {
        setSelected(null);
        setAnalysis(null);
        clearPreview();
      }
      await load();
    } catch (error: any) {
      setToast({
        type: "error",
        text: error.response?.data?.detail || "Failed to delete evidence items.",
      });
    } finally {
      setDeleteLoading(false);
    }
  }

  function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] || null;
    setUpload(file);
    setSelected(null);
    setAnalysis(null);
    clearPreview();
    if (file) setPreviewUrl(URL.createObjectURL(file));
  }

  async function uploadEvidence() {
    if (!upload) return;
    const form = new FormData();
    form.append("file", upload);
    const { data } = await api.post("/evidence/upload", form);
    setMessage(`Evidence #${data.id} uploaded.`);
    setUpload(null);
    await load();
  }

  async function selectEvidence(item: EvidenceItem) {
    try {
      setMessage("Loading evidence...");
      setSelected(item);
      setUpload(null);
      setAnalysis(null);
      clearPreview();
      const res = await api.get(`/files/evidence/${item.id}/download`, { responseType: "blob" });
      if (res.data && res.data.size > 0) {
        const url = URL.createObjectURL(res.data);
        setPreviewUrl(url);
        setMessage("");
      } else {
        setMessage("Failed to load evidence - file is empty.");
        setSelected(null);
      }
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || error.message || "Unknown error";
      setMessage(`Failed to load evidence: ${errorDetail}`);
      setSelected(null);
      console.error("Error loading evidence:", error);
    }
  }

  async function runObjectDetection() {
    const form = new FormData();
    if (selected) {
      form.append("evidence_id", String(selected.id));
    } else if (upload) {
      form.append("file", upload);
    } else {
      setMessage("Upload evidence or select a saved item first.");
      return;
    }
    setMessage("Running YOLOv8 object detection...");
    const { data } = await api.post<EvidenceAnalysisResult>("/evidence/object-detect", form);
    setAnalysis(data);
    setMessage(`${data.detections.length} object detections saved for evidence #${data.evidence_id}.`);
    await load();
  }

  function drawDetections() {
    const canvas = canvasRef.current;
    const data = analysis || liveResult;
    if (!canvas || !data) return;
    const media = imageRef.current?.complete ? imageRef.current : videoRef.current;
    if (!media) return;
    const rect = media.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width));
    canvas.height = Math.max(1, Math.round(rect.height));
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const scaleX = canvas.width / Math.max(data.frame_width, 1);
    const scaleY = canvas.height / Math.max(data.frame_height, 1);
    data.detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;
      const label = `${detection.class_name} ${(detection.confidence * 100).toFixed(0)}%`;
      ctx.strokeStyle = "#5E6B4F";
      ctx.lineWidth = 3;
      ctx.strokeRect(left, top, width, height);
      ctx.font = "700 13px Inter, sans-serif";
      const labelWidth = ctx.measureText(label).width + 14;
      ctx.fillStyle = "#5E6B4F";
      ctx.fillRect(left, Math.max(0, top - 26), labelWidth, 24);
      ctx.fillStyle = "#FFFFFF";
      ctx.fillText(label, left + 7, Math.max(16, top - 9));
    });
  }

  async function startLiveObjectDetection() {
    clearPreview();
    setSelected(null);
    setUpload(null);
    setAnalysis(null);
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 960, height: 540 }, audio: false });
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
    setLiveRunning(true);
    timerRef.current = window.setInterval(() => detectLiveFrame(), 650);
  }

  function stopLiveObjectDetection() {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setLiveRunning(false);
  }

  async function detectLiveFrame() {
    const video = videoRef.current;
    const capture = captureRef.current;
    if (!video || !capture || busyRef.current || video.readyState < 2) return;
    busyRef.current = true;
    try {
      const requestStarted = performance.now();
      const width = video.videoWidth || 960;
      const height = video.videoHeight || 540;
      capture.width = width;
      capture.height = height;
      const ctx = capture.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, width, height);
      const image = capture.toDataURL("image/jpeg", 0.78);
      setFrameSentCount((count) => count + 1);
      const { data } = await api.post<LiveObjectResult>("/evidence/object-detect-frame", { image, confidence });
      setLastResponseMs(Math.round(performance.now() - requestStarted));
      setBackendConnected(Boolean(data.success));
      setLastError("");
      setLiveResult(data);
    } catch (exc: any) {
      const error = exc.response?.data?.detail || exc.message || "Live object detection failed.";
      setLastError(error);
      setBackendConnected(false);
      setMessage(error);
    } finally {
      busyRef.current = false;
    }
  }

  function downloadAnalyzedImage() {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image || !analysis) {
      setMessage("Analyzed image download is available for image evidence after detection.");
      return;
    }
    const output = document.createElement("canvas");
    output.width = image.naturalWidth;
    output.height = image.naturalHeight;
    const ctx = output.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(image, 0, 0, output.width, output.height);
    const scaleX = output.width / Math.max(analysis.frame_width, 1);
    const scaleY = output.height / Math.max(analysis.frame_height, 1);
    analysis.detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      ctx.strokeStyle = "#5E6B4F";
      ctx.lineWidth = 4;
      ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
    });
    const url = output.toDataURL("image/png");
    const link = document.createElement("a");
    link.href = url;
    link.download = `motionguard-evidence-${analysis.evidence_id}-analyzed.png`;
    link.click();
  }

  const isVideo = previewUrl && (upload?.type.startsWith("video/") || selected?.evidence_type === "video");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Evidence Intelligence</h1>
        <p className="text-sm text-muted">Upload or select saved evidence, then run YOLOv8 object detection with saved analysis results.</p>
      </div>

      {toast && (
        <div className={`rounded-2xl border p-3 text-sm font-semibold ${toast.type === "success" ? "border-[#D1FAE5] bg-[#ECFDF5] text-[#15803D]" : "border-[#FEE2E2] bg-[#FEF2F2] text-[#DC2626]"}`}>
          {toast.text}
        </div>
      )}

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

      <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <Card>
          <div className="flex flex-wrap gap-3">
            <input className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10" placeholder="Object type" value={objectClass} onChange={(e) => setObjectClass(e.target.value)} />
            <Button onClick={load}>Search</Button>
            <label className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 text-sm font-semibold text-ink transition hover:border-[#5E6B4F] hover:bg-[#EFF2EC]">
              <Upload size={17} /> Upload evidence
              <input className="hidden" type="file" accept="image/*,video/*" onChange={handleUpload} />
            </label>
            <Button disabled={!upload} onClick={uploadEvidence}>Save upload</Button>
          </div>

          {items.length > 0 && (
            <div className="mt-3 flex gap-2">
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

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {items.map((item) => {
              const isSelectedItem = selectedIds.has(item.id);
              return (
                <div
                  key={item.id}
                  className={`rounded-[24px] border p-4 shadow-sm transition ${
                    selected?.id === item.id
                      ? "border-[#5E6B4F] bg-[#EFF2EC]"
                      : isSelectedItem
                        ? "border-[#5E6B4F] bg-[#F0F5ED]"
                        : "border-[#E5E7E1] bg-[#F7F8F4]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <button
                      className="flex flex-1 cursor-pointer flex-col text-left"
                      onClick={() => selectEvidence(item)}
                    >
                      <p className="font-bold text-ink">Evidence #{item.id}</p>
                      <p className="mt-2 text-sm text-muted">{item.object_class || "not analyzed"}</p>
                      <p className="text-sm text-muted">{formatLocalDateTime(item.created_at)}</p>
                      <div className="mt-4 flex gap-2">
                        <span className="rounded-full bg-[#EFF2EC] px-3 py-1 text-xs font-bold text-ink">{item.evidence_type}</span>
                      </div>
                    </button>
                    <input
                      type="checkbox"
                      checked={isSelectedItem}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleSelect(item.id);
                      }}
                      className="mt-1 h-5 w-5 cursor-pointer rounded accent-[#5E6B4F]"
                    />
                  </div>
                </div>
              );
            })}
          </div>
          {items.length === 0 && <p className="mt-5 rounded-2xl bg-[#EFF2EC] p-4 text-sm text-muted">No evidence available. Capture motion screenshots or analyze evidence to create records.</p>}
        </Card>

        <div className="space-y-4">
          <Card>
            <h2 className="font-bold text-ink">Object Detection</h2>
            <div className="mt-4 relative aspect-video overflow-hidden rounded-[24px] bg-[#1F2937]">
              {(previewUrl || liveRunning) && isVideo && <video ref={videoRef} className="h-full w-full object-fill" src={previewUrl || undefined} muted controls={Boolean(previewUrl)} playsInline onLoadedData={drawDetections} />}
              {liveRunning && !previewUrl && <video ref={videoRef} className="h-full w-full object-fill" muted playsInline />}
              {previewUrl && !isVideo && <img ref={imageRef} className="h-full w-full object-fill" src={previewUrl} onLoad={drawDetections} />}
              <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full" />
              {!previewUrl && <div className="absolute inset-0 grid place-items-center text-sm text-white/80">Select or upload evidence</div>}
            </div>
            <canvas ref={captureRef} className="hidden" />
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Button onClick={runObjectDetection}><ScanSearch size={18} /> Run object detection</Button>
              <Button onClick={downloadAnalyzedImage} className="bg-[#8A735A] hover:bg-[#76624B]"><Download size={18} /> Download analyzed</Button>
              <Button onClick={startLiveObjectDetection}><Camera size={18} /> Start live YOLO</Button>
              <Button onClick={stopLiveObjectDetection} className="bg-[#8A735A] hover:bg-[#76624B]"><Pause size={18} /> Stop live</Button>
            </div>
            <div className="mt-4 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-3">
              <div className="flex justify-between text-sm"><span className="font-semibold text-ink">YOLO confidence</span><span className="font-semibold text-muted">{confidence.toFixed(2)}</span></div>
              <input className="mt-2 w-full accent-[#5E6B4F]" type="range" min="0.15" max="0.7" step="0.05" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} />
              <label className="mt-3 flex items-center gap-2 text-sm font-semibold text-ink"><input type="checkbox" checked={debugMode} onChange={(event) => setDebugMode(event.target.checked)} /> Debug Mode</label>
            </div>
            {liveResult && <div className="mt-3 grid grid-cols-3 gap-2 text-sm"><Metric label="Humans" value={liveResult.human_count} /><Metric label="Objects" value={liveResult.object_count} /><Metric label="FPS" value={liveResult.fps.toFixed(1)} /></div>}
            {message && <p className="mt-3 rounded-2xl bg-[#EFF2EC] p-3 text-sm text-muted">{message}</p>}
          </Card>

          {debugMode && (
            <Card>
              <h2 className="font-bold text-ink">Debug Mode</h2>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <Metric label="Backend" value={backendConnected ? "Connected" : "Disconnected"} />
                <Metric label="Frames Sent" value={frameSentCount} />
                <Metric label="Response ms" value={lastResponseMs} />
                <Metric label="Frame Size" value={liveResult?.debug?.input_shape?.join(" x ") || "-"} />
                <Metric label="Model Loaded" value={liveResult?.debug?.model_loaded ? "Yes" : "-"} />
                <Metric label="Detections" value={liveResult?.debug?.detections_count ?? 0} />
                <Metric label="Inference ms" value={liveResult?.debug?.inference_ms ?? "-"} />
                <Metric label="Confidence" value={liveResult?.debug?.confidence ?? confidence} />
              </div>
              {lastError && <p className="mt-3 rounded-2xl bg-[#FEF2F2] p-3 text-sm text-[#DC2626]">{lastError}</p>}
            </Card>
          )}

          <Card>
            <h2 className="font-bold text-ink">Detection Results</h2>
            <div className="mt-3 space-y-2">
              {!analysis && <p className="text-sm text-muted">Run object detection to show labels, confidence, and bounding boxes.</p>}
              {(analysis?.detections || liveResult?.detections || []).map((detection, index) => (
                <div key={`${detection.class_name}-${index}`} className="flex items-center justify-between rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-3 text-sm">
                  <span className="font-bold text-ink">{detection.class_name}</span>
                  <span className="font-semibold text-muted">{(detection.confidence * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="font-bold text-ink">Evidence Actions</h2>
            <div className="mt-4 flex gap-2">
              <Button disabled={!selected} onClick={() => selected && download(selected.id)}><Download size={16} /> View original</Button>
              <button disabled={!selected} className="grid size-10 place-items-center rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] text-[#DC2626] disabled:opacity-40" onClick={() => selected && remove(selected.id)}><Trash2 size={16} /></button>
            </div>
          </Card>
        </div>
      </div>

      {deleteConfirmTarget === "bulk" && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#1F2937]/30 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-[24px] border border-[#E5E7E1] bg-[#FFFFFF] p-6 shadow-premium">
            <h2 className="text-lg font-bold text-ink">Delete selected evidence?</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Are you sure you want to delete {selectedIds.size} selected evidence item{selectedIds.size > 1 ? "s" : ""}? This action cannot be undone.</p>
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


function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-3"><p className="text-xs font-semibold uppercase text-muted">{label}</p><p className="mt-1 text-lg font-bold text-ink">{value}</p></div>;
}
