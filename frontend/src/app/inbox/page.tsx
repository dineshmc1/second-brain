"use client";

import { Archive, BrainCircuit, Check, FolderKanban, Inbox, ListTodo, Plus, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { InboxItem, Project } from "@/types";

const actions = [
  { key: "memory", label: "Memory", icon: BrainCircuit },
  { key: "task", label: "Task", icon: ListTodo },
  { key: "project", label: "Project", icon: FolderKanban },
] as const;

export default function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [content, setContent] = useState("");
  const [project, setProject] = useState("");
  const [busy, setBusy] = useState("");
  const load = async () => { const [inbox, projectList] = await Promise.all([api.inbox(), api.projects()]); setItems(inbox); setProjects(projectList); };
  useEffect(() => { void Promise.all([api.inbox(), api.projects()]).then(([inbox, projectList]) => { setItems(inbox); setProjects(projectList); }); }, []);
  const capture = async (event: FormEvent) => { event.preventDefault(); if (!content.trim()) return; await api.captureInbox(content.trim()); setContent(""); await load(); };
  const process = async (item: InboxItem, action: "memory" | "task" | "project" | "archive" | "discard") => { setBusy(item.id); try { await api.processInbox(item.id, action, project || undefined); await load(); } finally { setBusy(""); } };
  return <><PageHeader eyebrow="Capture pipeline" title="Smart Inbox" description="Collect first. Decide what each thought becomes when your attention is ready." action={<div className="rounded-full border border-cyan/20 bg-cyan/5 px-3 py-1 text-xs text-cyan">{items.length} unprocessed</div>}/>
    <div className="grid gap-6 p-8 xl:grid-cols-[380px_1fr]">
      <div className="space-y-5">
        <form onSubmit={capture} className="hud-panel rounded-2xl p-5"><div className="flex items-center gap-2"><Inbox size={17} className="text-cyan"/><h2 className="text-sm text-white">Capture a signal</h2></div><textarea value={content} onChange={event=>setContent(event.target.value)} rows={7} placeholder="Drop an idea, task, observation, question, or rough thought..." className="focus-ring mt-4 w-full resize-none rounded-xl border hairline bg-black/20 p-3 text-sm leading-6"/><button disabled={!content.trim()} className="mt-3 flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm text-void disabled:opacity-40"><Plus size={15}/> Add to inbox</button></form>
        <div className="glass rounded-2xl p-5"><label className="hud-label">Route into project</label><select value={project} onChange={event=>setProject(event.target.value)} className="mt-3 w-full rounded-xl border hairline bg-panel p-3 text-sm"><option value="">No project</option>{projects.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select><p className="mt-3 text-xs leading-5 text-muted">Applied when converting an inbox item into a memory or task.</p></div>
      </div>
      <section className="space-y-3">{items.map(item=><article key={item.id} className="hud-panel rounded-2xl p-5"><div className="flex flex-wrap items-start gap-4"><div className="min-w-0 flex-1"><div className="flex items-center gap-2"><span className="rounded-full border border-cyan/20 bg-cyan/5 px-2 py-1 text-[9px] uppercase tracking-wider text-cyan">Suggested {item.suggested_type}</span><span className="text-[10px] text-muted">{new Date(item.created_at).toLocaleString()}</span></div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-200">{item.content}</p></div><div className="flex flex-wrap gap-2">{actions.map(action=><button key={action.key} disabled={busy===item.id} onClick={()=>void process(item,action.key)} className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-2 text-xs ${item.suggested_type===action.key ? "border-cyan/35 bg-cyan/10 text-cyan" : "hairline text-muted hover:text-white"}`}><action.icon size={13}/>{action.label}</button>)}<button title="Archive" onClick={()=>void process(item,"archive")} className="rounded-lg border hairline p-2 text-muted hover:text-white"><Archive size={14}/></button><button title="Discard" onClick={()=>void process(item,"discard")} className="rounded-lg border border-red-400/10 p-2 text-red-300/70 hover:text-red-200"><Trash2 size={14}/></button></div></div>{busy===item.id&&<div className="mt-3 flex items-center gap-2 text-xs text-cyan"><Check size={13}/> Processing locally...</div>}</article>)}{!items.length&&<div className="grid min-h-72 place-items-center rounded-2xl border border-dashed hairline"><div className="text-center"><Check size={26} className="mx-auto text-mint"/><h2 className="mt-3 text-white">Inbox clear</h2><p className="mt-1 text-sm text-muted">Every captured thought has a destination.</p></div></div>}</section>
    </div>
  </>;
}
