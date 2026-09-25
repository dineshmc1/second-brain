"use client";

import { Activity, ArrowRight, BrainCircuit, CalendarDays, CheckCircle2, Circle, Inbox, Sparkles, Target } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { Overview } from "@/types";

function Metric({ label, value, suffix = "" }: { label: string; value: number; suffix?: string }) {
  return <div className="hud-panel rounded-xl p-4"><div className="hud-label">{label}</div><div className="data-value mt-3 text-2xl font-light text-white">{value}<span className="ml-1 text-xs text-cyan">{suffix}</span></div></div>;
}

export default function Home() {
  const [data, setData] = useState<Overview>();
  const [error, setError] = useState("");
  useEffect(() => { void api.overview().then(setData).catch(reason => setError(reason instanceof Error ? reason.message : "Core unavailable")); }, []);
  return <><PageHeader eyebrow="Command center" title="Good morning. Your mind is synchronized." description="A live briefing of commitments, learning progress, and the knowledge that needs attention." action={<Link href="/chat" className="flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void"><Sparkles size={15}/> Ask your brain</Link>}/>
    <div className="space-y-6 p-8">
      {error && <div className="rounded-xl border border-red-400/20 bg-red-400/5 p-4 text-sm text-red-200">{error}</div>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Memory nodes" value={data?.metrics.current_memories ?? 0}/><Metric label="Active projects" value={data?.metrics.active_projects ?? 0}/><Metric label="Mastered concepts" value={data?.metrics.mastered_nodes ?? 0}/><Metric label="Inbox signals" value={data?.inbox_count ?? 0}/>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
        <section className="hud-panel rounded-2xl p-6">
          <div className="flex items-center justify-between"><div><div className="hud-label">Daily briefing</div><h2 className="mt-2 text-lg text-white">Immediate focus</h2></div><Target className="text-cyan" size={20}/></div>
          <div className="mt-5 space-y-3">{data?.today_tasks.map(task => <Link href="/board" key={task.id} className="flex items-center gap-3 rounded-xl border hairline bg-black/15 p-3 transition hover:border-cyan/30"><Circle size={13} className="text-cyan"/><div className="min-w-0 flex-1"><div className="truncate text-sm text-white">{task.title}</div><div className="mt-1 text-[10px] uppercase tracking-wider text-muted">{task.project_name ?? "Independent"} · {task.priority}</div></div>{task.due_at && <time className="text-xs text-amber-200">{new Date(task.due_at).toLocaleDateString()}</time>}</Link>)}{!data?.today_tasks.length && <div className="rounded-xl border border-dashed hairline p-8 text-center text-sm text-muted">No active tasks. Your focus queue is clear.</div>}</div>
          <Link href="/board" className="mt-5 flex items-center gap-2 text-xs uppercase tracking-wider text-cyan">Open Kanban <ArrowRight size={13}/></Link>
        </section>
        <section className="hud-panel rounded-2xl p-6">
          <div className="flex items-center gap-3"><Activity size={18} className="text-mint"/><div><div className="hud-label">Weekly review</div><h2 className="mt-2 text-lg text-white">Momentum</h2></div></div>
          <div className="mt-7 flex items-end justify-between"><div className="data-value text-5xl font-extralight text-white">{data?.weekly.progress ?? 0}<span className="text-base text-cyan">%</span></div><div className="text-right text-xs leading-6 text-muted"><div>{data?.weekly.completed ?? 0} completed</div><div>{data?.weekly.remaining ?? 0} remaining</div></div></div>
          <div className="progress-track mt-4"><div className="progress-fill transition-all" style={{width:`${data?.weekly.progress ?? 0}%`}}/></div>
          <div className="mt-7 grid grid-cols-2 gap-3"><div className="rounded-xl border hairline bg-mint/[.03] p-3"><CheckCircle2 size={15} className="text-mint"/><strong className="mt-2 block text-xl font-light">{data?.weekly.completed ?? 0}</strong><span className="text-[9px] uppercase tracking-widest text-muted">Completed</span></div><Link href="/inbox" className="rounded-xl border hairline bg-cyan/[.03] p-3"><Inbox size={15} className="text-cyan"/><strong className="mt-2 block text-xl font-light">{data?.inbox_count ?? 0}</strong><span className="text-[9px] uppercase tracking-widest text-muted">Unprocessed</span></Link></div>
        </section>
      </div>
      <section className="hud-panel rounded-2xl p-6">
        <div className="flex items-center justify-between"><div><div className="hud-label">Google Calendar // Read only</div><h2 className="mt-2 text-lg text-white">Upcoming context</h2></div><CalendarDays size={19} className="text-cyan"/></div>
        {data?.calendar_error && <p className="mt-4 text-xs text-amber-200">Calendar sync: {data.calendar_error}</p>}
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{data?.calendar_events.slice(0,6).map(event => <article key={event.id} className="rounded-xl border hairline bg-black/15 p-4"><time className="text-[10px] uppercase tracking-wider text-cyan">{new Date(event.start).toLocaleString([], {weekday:"short",month:"short",day:"numeric",hour:event.all_day ? undefined : "numeric",minute:event.all_day ? undefined : "2-digit"})}</time><h3 className="mt-2 text-sm text-white">{event.title}</h3>{event.location && <p className="mt-1 truncate text-xs text-muted">{event.location}</p>}</article>)}{!data?.calendar_events.length && <Link href="/settings" className="col-span-full flex items-center justify-center gap-2 rounded-xl border border-dashed hairline p-7 text-sm text-muted hover:text-cyan"><BrainCircuit size={16}/> Connect a private Google Calendar iCal feed in Settings</Link>}</div>
      </section>
    </div>
  </>;
}
