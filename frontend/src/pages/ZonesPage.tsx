import { ChangeEvent, MouseEvent, useEffect, useRef, useState } from "react";
import { Camera, MousePointer2, Pause, Pentagon, Play, Save, Square, Trash2, Upload, X } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../services/api";

type Point = { x: number; y: number };
type DrawMode = "polygon" | "rectangle";
type DetectMode = "motion" | "object" | "both";
type Zone = { id: number; name: string; zone_type: string; coordinates: Point[]; source_type: string };
type MotionBox = { bbox: number[]; area: number; inside_zone: boolean };
type ObjectBox = { class_name: string; confidence: number; bbox: number[]; inside_zone: boolean };

export function ZonesPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const captureRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const busyRef = useRef(false);
  const [zones, setZones] = useState<Zone[]>([]);
  const [points, setPoints] = useState<Point[]>([]);
  const [rectStart, setRectStart] = useState<Point | null>(null);
  const [drawMode, setDrawMode] = useState<DrawMode>("polygon");
  const [detectMode, setDetectMode] = useState<DetectMode>("motion");
  const [activeZoneId, setActiveZoneId] = useState<number | "">("");
  const [sourceType, setSourceType] = useState("webcam");
  const [name, setName] = useState("Restricted Zone");
  const [zoneType, setZoneType] = useState("Restricted Area");
  const [previewUrl, setPreviewUrl] = useState("");
  const [monitoring, setMonitoring] = useState(false);
  const [message, setMessage] = useState("");
  const [motion, setMotion] = useState<any>(null);
  const [objects, setObjects] = useState<any>(null);
  const [alerts, setAlerts] = useState<string[]>([]);

  const load = () => api.get("/zones").then((res) => {
    setZones(res.data);
    if (!activeZoneId && res.data.length) setActiveZoneId(res.data[0].id);
  });

  useEffect(() => { load(); return () => stopAll(); }, []);
  useEffect(() => { drawOverlay(); }, [zones, activeZoneId, points, motion, objects]);

  async function startWebcam() {
    setSourceType("webcam");
    setMessage("");
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
    streamRef.current = stream;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl("");
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
  }

  function stopAll() {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setMonitoring(false);
  }

  function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    stopAll();
    setSourceType("upload");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
    if (videoRef.current) videoRef.current.srcObject = null;
    setTimeout(() => videoRef.current?.play().catch(() => undefined), 100);
  }

  function normalizedPoint(event: MouseEvent<HTMLDivElement>): Point {
    const rect = event.currentTarget.getBoundingClientRect();
    return { x: Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)), y: Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)) };
  }

  function onCanvasClick(event: MouseEvent<HTMLDivElement>) {
    const point = normalizedPoint(event);
    if (drawMode === "polygon") return setPoints([...points, point]);
    if (!rectStart) {
      setRectStart(point);
      setPoints([point]);
    } else {
      const x1 = Math.min(rectStart.x, point.x), y1 = Math.min(rectStart.y, point.y);
      const x2 = Math.max(rectStart.x, point.x), y2 = Math.max(rectStart.y, point.y);
      setPoints([{ x: x1, y: y1 }, { x: x2, y: y1 }, { x: x2, y: y2 }, { x: x1, y: y2 }]);
      setRectStart(null);
    }
  }

  async function save() {
    if (points.length < 3) return;
    await api.post("/zones", { name, zone_type: zoneType, source_type: sourceType, coordinates: points });
    setPoints([]);
    setRectStart(null);
    await load();
  }

  async function remove(id: number) {
    await api.delete(`/zones/${id}`);
    await load();
  }

  function startMonitoring() {
    if (!activeZoneId) return setMessage("Select an active zone first.");
    setMonitoring(true);
    timerRef.current = window.setInterval(() => analyzeZoneFrame(), detectMode === "object" ? 750 : 450);
  }

  async function analyzeZoneFrame() {
    const video = videoRef.current, capture = captureRef.current;
    if (!video || !capture || busyRef.current || video.readyState < 2 || !activeZoneId) return;
    busyRef.current = true;
    try {
      const width = video.videoWidth || 960, height = video.videoHeight || 540;
      capture.width = width; capture.height = height;
      const ctx = capture.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, width, height);
      const image = capture.toDataURL("image/jpeg", 0.78);
      if (detectMode === "motion") {
        const { data } = await api.post(`/zones/${activeZoneId}/motion-frame`, { image, min_area: 900, cooldown_seconds: 15 });
        setMotion(data);
        setObjects(null);
        if (data.event_created) setAlerts((items) => [`Motion detected in ${data.zone_name}`, ...items].slice(0, 6));
      } else if (detectMode === "object") {
        const { data } = await api.post(`/zones/${activeZoneId}/object-frame`, { image, confidence: 0.25, cooldown_seconds: 15 });
        setObjects(data);
        setMotion(null);
        if (data.event_created) setAlerts((items) => [`Object detected in ${data.zone_name}`, ...items].slice(0, 6));
      } else {
        const { data } = await api.post(`/zones/${activeZoneId}/analyze-frame`, { image, min_area: 900, confidence: 0.25, cooldown_seconds: 15 });
        setMotion({ ...data.motion, frame_width: data.frame_width, frame_height: data.frame_height, fps: data.fps });
        setObjects({ ...data.objects, frame_width: data.frame_width, frame_height: data.frame_height, fps: data.fps });
        if (data.event_created) setAlerts((items) => [`Zone event in ${data.zone_name}`, ...items].slice(0, 6));
      }
    } catch (exc: any) {
      setMessage(exc.response?.data?.detail || exc.message || "Zone monitoring failed.");
    } finally {
      busyRef.current = false;
    }
  }

  function drawOverlay() {
    const video = videoRef.current, canvas = canvasRef.current;
    if (!video || !canvas) return;
    const rect = video.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width));
    canvas.height = Math.max(1, Math.round(rect.height));
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const active = zones.find((zone) => zone.id === activeZoneId);
    if (active) drawZone(ctx, active.coordinates, canvas.width, canvas.height);
    (motion?.motion_boxes || []).forEach((box: MotionBox) => drawBox(ctx, box.bbox, motion.frame_width, motion.frame_height, "#D97706", "motion"));
    (objects?.detections || []).forEach((item: ObjectBox) => drawBox(ctx, item.bbox, objects.frame_width, objects.frame_height, "#5E6B4F", `${item.class_name} ${(item.confidence * 100).toFixed(0)}%`));
  }

  const currentPolygon = points.map((p) => `${p.x * 100},${p.y * 100}`).join(" ");

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-ink">Virtual Zones</h1><p className="text-sm text-muted">Draw zones, select an active zone, then monitor motion or YOLO objects inside that zone only.</p></div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_.85fr]">
        <Card className="overflow-hidden p-3">
          <div onClick={onCanvasClick} className="relative aspect-video cursor-crosshair overflow-hidden rounded-[24px] bg-[#1F2937]">
            <video ref={videoRef} className="h-full w-full object-fill" src={previewUrl || undefined} muted playsInline controls={sourceType === "upload"} />
            <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full" />
            <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              {zones.map((zone) => <polygon key={zone.id} points={zone.coordinates.map((p) => `${p.x * 100},${p.y * 100}`).join(" ")} fill={zone.id === activeZoneId ? "rgba(21,128,61,.16)" : "rgba(94,107,79,.10)"} stroke={zone.id === activeZoneId ? "#15803D" : "#5E6B4F"} strokeWidth=".45" />)}
              {points.length > 1 && <polygon points={currentPolygon} fill="rgba(94,107,79,.16)" stroke="#5E6B4F" strokeWidth=".55" />}
              {points.map((p, index) => <circle key={index} cx={p.x * 100} cy={p.y * 100} r="1.1" fill="#5E6B4F" />)}
            </svg>
            {!previewUrl && !streamRef.current && <div className="absolute inset-0 grid place-items-center text-sm text-white/80">Open webcam or upload video</div>}
          </div>
          <canvas ref={captureRef} className="hidden" />
        </Card>

        <div className="space-y-4">
          <Card>
            <h2 className="font-bold text-ink">Source & Drawing</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Button onClick={startWebcam}><Camera size={18} /> Webcam</Button>
              <label className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 text-sm font-semibold text-ink transition hover:border-[#5E6B4F] hover:bg-[#EFF2EC]"><Upload size={18} /> Upload<input className="hidden" type="file" accept="video/*" onChange={handleUpload} /></label>
              <button className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl border px-4 text-sm font-semibold ${drawMode === "polygon" ? "border-[#5E6B4F] bg-[#EFF2EC]" : "border-[#E5E7E1] bg-[#F7F8F4]"}`} onClick={() => setDrawMode("polygon")}><Pentagon size={17} /> Polygon</button>
              <button className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl border px-4 text-sm font-semibold ${drawMode === "rectangle" ? "border-[#5E6B4F] bg-[#EFF2EC]" : "border-[#E5E7E1] bg-[#F7F8F4]"}`} onClick={() => setDrawMode("rectangle")}><Square size={17} /> Rectangle</button>
            </div>
            <button className="mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-4 text-sm font-semibold text-ink" onClick={() => { setPoints([]); setRectStart(null); }}><X size={17} /> Clear drawing</button>
          </Card>

          <Card>
            <h2 className="font-bold text-ink">Zone Monitor</h2>
            <div className="mt-4 space-y-3">
              <select className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2" value={activeZoneId} onChange={(event) => setActiveZoneId(Number(event.target.value))}>
                <option value="">Select active zone</option>
                {zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}
              </select>
              <select className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2" value={detectMode} onChange={(event) => setDetectMode(event.target.value as DetectMode)}>
                <option value="motion">Motion Only</option><option value="object">Object Only</option><option value="both">Motion + Object</option>
              </select>
              <div className="grid grid-cols-2 gap-3"><Button onClick={startMonitoring}><Play size={18} /> Start</Button><Button onClick={stopAll} className="bg-[#8A735A] hover:bg-[#76624B]"><Pause size={18} /> Stop</Button></div>
              <div className="grid grid-cols-2 gap-2 text-sm"><Metric label="Motion FPS" value={motion?.fps?.toFixed?.(1) || "0.0"} /><Metric label="Object FPS" value={objects?.fps?.toFixed?.(1) || "0.0"} /><Metric label="Moving Subjects" value={motion?.estimated_moving_subjects || 0} /><Metric label="Objects" value={objects?.object_count || 0} /></div>
            </div>
          </Card>

          <Card>
            <h2 className="font-bold text-ink">Save Zone</h2>
            <div className="mt-4 space-y-3">
              <input className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} />
              <select className="w-full rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2" value={zoneType} onChange={(e) => setZoneType(e.target.value)}><option>Restricted Area</option><option>Entry Gate</option><option>Parking Area</option><option>Sensitive Area</option></select>
              <Button onClick={save} disabled={points.length < 3}><Save size={18} /> Save zone</Button>
              {message && <p className="rounded-2xl bg-[#FEF2F2] p-3 text-sm text-[#DC2626]">{message}</p>}
            </div>
          </Card>
        </div>
      </div>

      <Card>
        <h2 className="mb-4 flex items-center gap-2 font-bold text-ink"><MousePointer2 size={18} /> Saved Zones & Alerts</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {zones.map((zone) => <div key={zone.id} className="rounded-[24px] border border-[#E5E7E1] bg-[#F7F8F4] p-4 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{zone.name}</p><p className="text-sm text-muted">{zone.zone_type} - {zone.coordinates.length} points</p></div><button onClick={() => remove(zone.id)} className="grid size-9 place-items-center rounded-2xl border border-[#FEE2E2] bg-[#FEF2F2] text-[#DC2626]"><Trash2 size={16} /></button></div></div>)}
        </div>
        <div className="mt-4 space-y-2">{alerts.map((alert, index) => <p key={`${alert}-${index}`} className="rounded-2xl bg-[#FEF2F2] p-3 text-sm font-semibold text-[#DC2626]">{alert}</p>)}</div>
      </Card>
    </div>
  );
}

function drawZone(ctx: CanvasRenderingContext2D, points: Point[], width: number, height: number) {
  if (points.length < 3) return;
  ctx.beginPath();
  points.forEach((point, index) => index ? ctx.lineTo(point.x * width, point.y * height) : ctx.moveTo(point.x * width, point.y * height));
  ctx.closePath();
  ctx.strokeStyle = "#15803D";
  ctx.lineWidth = 3;
  ctx.stroke();
}

function drawBox(ctx: CanvasRenderingContext2D, box: number[], frameWidth: number, frameHeight: number, color: string, label: string) {
  const scaleX = ctx.canvas.width / Math.max(frameWidth, 1), scaleY = ctx.canvas.height / Math.max(frameHeight, 1);
  const [x1, y1, x2, y2] = box;
  const left = x1 * scaleX, top = y1 * scaleY, width = (x2 - x1) * scaleX, height = (y2 - y1) * scaleY;
  ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.strokeRect(left, top, width, height);
  ctx.font = "700 13px Inter, sans-serif";
  const labelWidth = ctx.measureText(label).width + 14;
  ctx.fillStyle = color; ctx.fillRect(left, Math.max(0, top - 26), labelWidth, 24);
  ctx.fillStyle = "#FFFFFF"; ctx.fillText(label, left + 7, Math.max(16, top - 9));
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] p-3"><p className="text-xs font-semibold uppercase text-muted">{label}</p><p className="mt-1 text-lg font-bold text-ink">{value}</p></div>;
}
