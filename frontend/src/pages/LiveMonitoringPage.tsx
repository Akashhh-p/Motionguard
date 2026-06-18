import { ChangeEvent, useEffect, useRef, useState } from "react";
import { AlertTriangle, Camera, Pause, Upload, Video } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../services/api";


type MotionBox = { bbox: number[]; area: number };
type MotionResult = {
  success?: boolean;
  motion_detected: boolean;
  motion_boxes: MotionBox[];
  fps: number;
  frame_width: number;
  frame_height: number;
  motion_count: number;
  estimated_moving_subjects: number;
  motion_area_total: number;
  motion_events_today: number;
  alerts: { zone_name: string }[];
};


const emptyResult: MotionResult = {
  motion_detected: false,
  motion_boxes: [],
  fps: 0,
  frame_width: 0,
  frame_height: 0,
  motion_count: 0,
  estimated_moving_subjects: 0,
  motion_area_total: 0,
  motion_events_today: 0,
  alerts: [],
};


export function LiveMonitoringPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const busyRef = useRef(false);
  const lastResponseAtRef = useRef(0);
  const [running, setRunning] = useState(false);
  const [source, setSource] = useState<"webcam" | "upload">("webcam");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [message, setMessage] = useState("");
  const [frontendFps, setFrontendFps] = useState(0);
  const [result, setResult] = useState<MotionResult>(emptyResult);

  useEffect(() => () => stopMonitoring(), []);

  useEffect(() => {
    drawOverlay(result);
  }, [result]);

  async function startWebcam() {
    setSource("webcam");
    setMessage("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
      streamRef.current = stream;
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl("");
      }
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setRunning(true);
      startFrameLoop();
    } catch (exc: any) {
      setMessage(exc.message || "Could not open webcam. Check browser camera permissions.");
    }
  }

  function stopMonitoring() {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setRunning(false);
  }

  function startFrameLoop() {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(() => analyzeCurrentFrame(), 400);
  }

  async function analyzeCurrentFrame() {
    const video = videoRef.current;
    const capture = captureCanvasRef.current;
    if (!video || !capture || busyRef.current || video.readyState < 2) return;
    busyRef.current = true;
    try {
      const width = video.videoWidth || 960;
      const height = video.videoHeight || 540;
      capture.width = width;
      capture.height = height;
      const context = capture.getContext("2d");
      if (!context) return;
      context.drawImage(video, 0, 0, width, height);
      const image = capture.toDataURL("image/jpeg", 0.78);
      const { data } = await api.post<MotionResult>("/motion/frame", {
        image,
        source_type: source,
        resize_width: 640,
      });
      const now = performance.now();
      if (lastResponseAtRef.current) {
        setFrontendFps(Number((1000 / Math.max(now - lastResponseAtRef.current, 1)).toFixed(1)));
      }
      lastResponseAtRef.current = now;
      setResult(data);
      setMessage("");
    } catch (exc: any) {
      const error = exc.response?.data?.detail || exc.message || "Motion detection failed.";
      setMessage(error);
    } finally {
      busyRef.current = false;
    }
  }

  function drawOverlay(data: MotionResult) {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    const rect = video.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width));
    canvas.height = Math.max(1, Math.round(rect.height));
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const scaleX = canvas.width / Math.max(data.frame_width || video.videoWidth || canvas.width, 1);
    const scaleY = canvas.height / Math.max(data.frame_height || video.videoHeight || canvas.height, 1);

    data.motion_boxes.forEach((box) => {
      const [x1, y1, x2, y2] = box.bbox;
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;
      ctx.strokeStyle = "#D97706";
      ctx.lineWidth = 3;
      ctx.setLineDash([7, 5]);
      ctx.strokeRect(left, top, width, height);
      ctx.setLineDash([]);
      const label = `motion ${Math.round(box.area)}px`;
      ctx.font = "700 13px Inter, sans-serif";
      const labelWidth = ctx.measureText(label).width + 14;
      ctx.fillStyle = "#D97706";
      ctx.fillRect(left, Math.max(0, top - 26), labelWidth, 24);
      ctx.fillStyle = "#FFFFFF";
      ctx.fillText(label, left + 7, Math.max(16, top - 9));
    });
  }

  function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0] || null;
    setFile(next);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (next) {
      setSource("upload");
      setPreviewUrl(URL.createObjectURL(next));
      stopMonitoring();
      if (videoRef.current) videoRef.current.srcObject = null;
      setTimeout(() => videoRef.current?.play().catch(() => undefined), 100);
    }
  }

  function startUploadedVideoMonitoring() {
    if (!file) return;
    setSource("upload");
    setRunning(true);
    videoRef.current?.play().catch(() => undefined);
    startFrameLoop();
  }

  const liveFps = frontendFps || result.fps || 0;
  const lowFps = running && liveFps > 0 && liveFps < 8;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-ink">Live Monitoring</h1>
          <p className="text-sm text-muted">Real-time OpenCV motion detection with zone-aware event capture. YOLO analysis lives in Evidence.</p>
        </div>
        <div className="rounded-full border border-[#E5E7E1] bg-[#F7F8F4] px-4 py-2 text-sm font-semibold text-ink shadow-sm">Active source: {source}</div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.45fr_.75fr]">
        <Card className="overflow-hidden p-3">
          <div className="relative aspect-video overflow-hidden rounded-[24px] bg-[#1F2937] shadow-inner">
            <video ref={videoRef} className="h-full w-full object-fill" src={previewUrl || undefined} muted playsInline controls={source === "upload"} />
            <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full" />
            {!running && !previewUrl && <div className="absolute inset-0 grid place-items-center text-sm text-white/80">Start webcam or upload a video</div>}
          </div>
          <canvas ref={captureCanvasRef} className="hidden" />
        </Card>

        <div className="space-y-4">
          <Card>
            <h2 className="font-bold text-ink">Motion Control</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <Button onClick={startWebcam}><Camera size={18} /> Start webcam</Button>
              <Button onClick={stopMonitoring} className="bg-[#8A735A] hover:bg-[#76624B]"><Pause size={18} /> Stop monitoring</Button>
            </div>
            <label className="mt-4 flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-2xl border border-dashed border-[#E5E7E1] bg-[#F7F8F4] px-4 text-sm font-semibold text-ink transition hover:border-[#5E6B4F] hover:bg-[#EFF2EC]">
              <Upload size={18} /> Upload video for motion
              <input className="hidden" type="file" accept="video/mp4,video/quicktime,video/x-msvideo,video/*" onChange={handleUpload} />
            </label>
            <Button disabled={!file} onClick={startUploadedVideoMonitoring} className="mt-3 w-full"><Video size={18} /> Monitor uploaded video</Button>
          </Card>

          <Card>
            <h2 className="font-bold text-ink">Telemetry</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="FPS" value={liveFps.toFixed(1)} tone={lowFps ? "warn" : undefined} />
              <Metric label="Motion Boxes" value={result.motion_count || 0} />
              <Metric label="Status" value={result.motion_detected ? "Motion detected" : "No motion"} tone={result.motion_detected ? "warn" : "ok"} />
              <Metric label="Capture" value={running ? "Running" : "Stopped"} tone={running ? "ok" : undefined} />
              <Metric label="Estimated Moving Subjects" value={result.estimated_moving_subjects || 0} />
              <Metric label="Motion Area" value={result.motion_area_total || 0} />
              <Metric label="Events Today" value={result.motion_events_today || 0} />
            </div>
            {lowFps && <p className="mt-3 rounded-2xl bg-[#FEF3C7] p-3 text-sm font-semibold text-[#D97706]">FPS is low. Reduce camera resolution or close other heavy apps.</p>}
          </Card>

          <Card>
            <h2 className="flex items-center gap-2 font-bold text-ink"><AlertTriangle size={18} /> Zone Alerts</h2>
            <div className="mt-3 space-y-2">
              {result.alerts.length === 0 && <p className="text-sm text-muted">No restricted-zone motion alerts.</p>}
              {result.alerts.map((alert, index) => (
                <div key={`${alert.zone_name}-${index}`} className="rounded-2xl border border-[#FEE2E2] bg-[#FEF2F2] p-3 text-sm font-semibold text-[#DC2626]">
                  Motion entered {alert.zone_name}
                </div>
              ))}
              {message && <p className="rounded-2xl bg-[#EFF2EC] p-3 text-sm text-muted">{message}</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}


function Metric({ label, value, tone }: { label: string; value: string | number; tone?: "ok" | "warn" }) {
  return (
    <div className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-3 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-1 text-lg font-bold ${tone === "warn" ? "text-[#D97706]" : tone === "ok" ? "text-[#15803D]" : "text-ink"}`}>{value}</p>
    </div>
  );
}
