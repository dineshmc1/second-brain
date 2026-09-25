"use client";

import { ArrowLeft, CalendarDays, Check, Database, Download, Gauge, KeyRound, Loader2, LockKeyhole, Save, Volume2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";

function Section({ title, icon: Icon, children }: { title: string; icon: typeof KeyRound; children: React.ReactNode }) { return <section className="glass rounded-2xl p-6"><div className="mb-5 flex items-center gap-3"><Icon size={18} className="text-cyan"/><h2 className="text-sm font-medium text-white">{title}</h2></div>{children}</section>; }
function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) { return <label className="flex items-center justify-between py-2 text-sm text-slate-300"><span>{label}</span><button type="button" onClick={() => onChange(!checked)} className={`relative h-6 w-11 rounded-full transition ${checked ? "bg-cyan" : "bg-white/10"}`}><span className={`absolute top-1 h-4 w-4 rounded-full bg-void transition ${checked ? "left-6" : "left-1"}`}/></button></label>; }

export default function SettingsPage() {
  const router = useRouter();
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [key, setKey] = useState("");
  const [calendarUrl, setCalendarUrl] = useState("");
  const [saved, setSaved] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState("");
  useEffect(() => { void api.settings().then(setValues); }, []);
  const save = async (event: FormEvent) => {
    event.preventDefault();
    const result = await api.saveSettings(values, key || undefined, calendarUrl || undefined);
    setValues(result); setKey(""); setCalendarUrl("");
    try { const autostart = await import("@tauri-apps/plugin-autostart"); if (values.launch_on_startup) await autostart.enable(); else await autostart.disable(); } catch { /* Browser development mode has no Tauri runtime. */ }
    setSaved(true); setTimeout(() => setSaved(false), 1800);
  };
  const set = (name: string, value: unknown) => setValues(current => ({ ...current, [name]: value }));
  const exportData = async () => {
    setExporting(true); setExportStatus("");
    try {
      const { blob, filename } = await api.exportData();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = filename; link.style.display = "none";
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setExportStatus(`Saved ${filename}. You can continue using the app.`);
    } catch (error) {
      setExportStatus(error instanceof Error ? error.message : "Export failed");
    } finally { setExporting(false); }
  };

  return <form onSubmit={save}><PageHeader eyebrow="System control" title="Settings" description="Tune intelligence, privacy, voice, and desktop behaviour." action={<div className="flex items-center gap-2"><button type="button" onClick={() => router.back()} className="flex items-center gap-2 rounded-xl border hairline px-3 py-2 text-sm text-muted hover:text-white"><ArrowLeft size={15}/> Back</button><button className="flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void">{saved ? <Check size={16}/> : <Save size={16}/>} {saved ? "Saved" : "Save changes"}</button></div>}/>
    <div className="grid gap-5 p-8 lg:grid-cols-2">
      <Section title="AI" icon={KeyRound}><label className="block text-xs text-muted">OpenRouter API key</label><input value={key} onChange={event => setKey(event.target.value)} type="password" placeholder={Boolean(values.has_api_key) ? "Stored securely — enter to replace" : "sk-or-v1-…"} className="focus-ring mt-2 w-full rounded-xl border hairline bg-black/20 px-3 py-2.5 text-sm"/><p className="mt-2 text-[10px] text-muted">Saved in Windows Credential Manager, never in the frontend or database.</p><label className="mt-5 block text-xs text-muted">OpenRouter model</label><input value={String(values.model ?? "openai/gpt-5.4-nano")} onChange={event => set("model", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-black/20 px-3 py-2.5 text-sm"/></Section>
      <Section title="AI cost control" icon={Gauge}><Toggle label="Cache identical AI work" checked={Boolean(values.ai_cache ?? true)} onChange={value => set("ai_cache", value)}/><label className="mt-4 block text-xs text-muted">Maximum paid AI calls per day: {Number(values.daily_ai_budget ?? 12)}</label><input type="range" min="1" max="50" value={Number(values.daily_ai_budget ?? 12)} onChange={event => set("daily_ai_budget", Number(event.target.value))} className="mt-2 w-full accent-cyan"/><label className="mt-4 block text-xs text-muted">Default learning depth</label><select value={String(values.ai_depth ?? "quick")} onChange={event => set("ai_depth", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-panel px-3 py-2.5 text-sm"><option value="quick">Quick · lowest tokens</option><option value="standard">Standard</option><option value="deep">Deep</option></select><p className="mt-3 text-[10px] leading-5 text-muted">Local heuristics run first. Only explicit generation actions call OpenRouter; repeated requests use the local cache.</p></Section>
      <Section title="Google Calendar · read only" icon={CalendarDays}><label className="block text-xs text-muted">Secret address in iCal format</label><input value={calendarUrl} onChange={event => setCalendarUrl(event.target.value)} type="password" placeholder={Boolean(values.has_calendar) ? "Stored securely — enter to replace" : "https://calendar.google.com/calendar/ical/.../basic.ics"} className="focus-ring mt-2 w-full rounded-xl border hairline bg-black/20 px-3 py-2.5 text-sm"/><p className="mt-3 text-[10px] leading-5 text-muted">Used only to read upcoming events for briefings. Stored in Windows Credential Manager. Second Brain cannot create, edit, or reply to calendar events.</p></Section>
      <Section title="Memory & retrieval" icon={Database}><Toggle label="Automatic memory" checked={Boolean(values.auto_memory ?? true)} onChange={value => set("auto_memory", value)}/><Toggle label="Ask before saving" checked={Boolean(values.ask_before_saving ?? false)} onChange={value => set("ask_before_saving", value)}/><label className="mt-4 block text-xs text-muted">Retrieved sources: {Number(values.top_k ?? 8)}</label><input type="range" min="3" max="20" value={Number(values.top_k ?? 8)} onChange={event => set("top_k", Number(event.target.value))} className="mt-2 w-full accent-cyan"/></Section>
      <Section title="Voice" icon={Volume2}><label className="block text-xs text-muted">Response mode</label><select value={String(values.response_mode ?? "text")} onChange={event => set("response_mode", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-panel px-3 py-2.5 text-sm"><option value="text">Text only</option><option value="voice">Voice only</option><option value="both">Text + voice</option></select><Toggle label="Auto-read responses" checked={Boolean(values.auto_read ?? false)} onChange={value => set("auto_read", value)}/><p className="mt-3 text-[10px] leading-5 text-muted">Voice replies use an installed Windows voice. Microphone transcription uses the bundled local Whisper model and may take a few seconds on CPU.</p></Section>
      <Section title="Privacy & portability" icon={LockKeyhole}><div className="space-y-2 text-xs text-slate-300">{["Documents stored locally", "Embeddings computed locally", "Database stored locally", "Only retrieved context sent through OpenRouter"].map(item => <div key={item} className="flex items-center gap-2"><Check size={13} className="text-mint"/>{item}</div>)}</div><button type="button" onClick={() => void exportData()} disabled={exporting} className="mt-5 flex items-center gap-2 rounded-xl border hairline px-3 py-2 text-xs text-cyan hover:bg-cyan/5 disabled:opacity-50">{exporting ? <Loader2 size={14} className="animate-spin"/> : <Download size={14}/>} {exporting ? "Preparing export…" : "Export Second Brain"}</button>{exportStatus && <p className="mt-3 text-xs text-muted">{exportStatus}</p>}</Section>
      <Section title="Windows & appearance" icon={Save}><Toggle label="Launch on Windows startup" checked={Boolean(values.launch_on_startup ?? false)} onChange={value => set("launch_on_startup", value)}/><Toggle label="Minimize to system tray" checked={Boolean(values.close_to_tray ?? true)} onChange={value => set("close_to_tray", value)}/><Toggle label="Interface animations" checked={Boolean(values.animations ?? true)} onChange={value => set("animations", value)}/><div className="mt-4 rounded-xl border hairline bg-black/20 p-3 text-xs text-muted"><div>Quick search: <kbd className="text-cyan">Ctrl + Space</kbd> (press again or Esc to close)</div><div className="mt-2">Quick capture: <kbd className="text-cyan">Ctrl + Alt + M</kbd> (press again or Esc to close)</div></div></Section>
    </div>
  </form>;
}
