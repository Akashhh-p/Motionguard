import { useEffect, useState } from "react";
import { LogOut, Save } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState<any | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => { api.get("/settings").then((res) => setSettings(res.data)); }, []);
  if (!settings) return <p className="text-muted">Loading settings...</p>;

  async function save() {
    await api.put("/settings", settings);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  }

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-ink">Settings</h1><p className="text-sm text-muted">Account, detection, alert, and evidence preferences.</p></div>
      <div className="grid gap-4 lg:grid-cols-[.8fr_1.2fr]">
        <Card>
          <h2 className="font-bold text-ink">Account</h2>
          <div className="mt-4 space-y-2 text-sm text-muted">
            <p>Name: <b>{user?.full_name}</b></p>
            <p>Email: <b>{user?.email}</b></p>
            <p>Provider: <b>{user?.auth_provider}</b></p>
          </div>
          <Button onClick={logout} className="mt-5 bg-[#DC2626] hover:bg-[#B91C1C]"><LogOut size={18} /> Logout</Button>
        </Card>
        <Card>
          <h2 className="font-bold text-ink">Detection engine</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="text-sm text-muted">Confidence threshold<input type="number" step="0.05" min="0.05" max="0.95" className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.confidence_threshold} onChange={(e) => setSettings({ ...settings, confidence_threshold: Number(e.target.value) })} /></label>
            <label className="text-sm text-muted">Frame skip<input type="number" min="1" max="30" className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.frame_skip} onChange={(e) => setSettings({ ...settings, frame_skip: Number(e.target.value) })} /></label>
            <label className="text-sm text-muted">Detection sensitivity<input type="number" step="0.05" min="0.1" max="1" className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.detection_sensitivity} onChange={(e) => setSettings({ ...settings, detection_sensitivity: Number(e.target.value) })} /></label>
            <label className="text-sm text-muted">Theme<select className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.theme} onChange={(e) => setSettings({ ...settings, theme: e.target.value })}><option>Premium Sage Stone</option></select></label>
            <label className="flex items-center gap-2 text-sm text-muted"><input type="checkbox" checked={settings.alert_sound} onChange={(e) => setSettings({ ...settings, alert_sound: e.target.checked })} /> Alert sound</label>
            <label className="flex items-center gap-2 text-sm text-muted"><input type="checkbox" checked={settings.evidence_capture} onChange={(e) => setSettings({ ...settings, evidence_capture: e.target.checked })} /> Evidence capture</label>
            <label className="flex items-center gap-2 text-sm text-muted"><input type="checkbox" checked={settings.video_clip_save} onChange={(e) => setSettings({ ...settings, video_clip_save: e.target.checked })} /> Video clip save</label>
            <label className="text-sm text-muted">Screenshot folder<input className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.screenshot_save_folder} onChange={(e) => setSettings({ ...settings, screenshot_save_folder: e.target.value })} /></label>
          </div>
          <label className="mt-4 block text-sm text-muted">Allowed object classes<input className="mt-1 w-full rounded-lg border border-[#E5E7E1] bg-[#F7F8F4] px-3 py-2 text-ink outline-none focus:border-[#5E6B4F]" value={settings.allowed_object_classes.join(",")} onChange={(e) => setSettings({ ...settings, allowed_object_classes: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} /></label>
          <div className="mt-5 flex items-center gap-3"><Button onClick={save}><Save size={18} /> Save settings</Button>{saved && <span className="text-sm font-semibold text-teal">Saved</span>}</div>
        </Card>
      </div>
    </div>
  );
}
