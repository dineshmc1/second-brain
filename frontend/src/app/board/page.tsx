"use client";

import { Bot, CalendarClock, GripVertical, Plus, Sparkles, Trash2, WandSparkles } from "lucide-react";
import { DragEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { Project, Task } from "@/types";

const columns = [
  { key: "backlog", label: "Backlog", hint: "Unsorted work" },
  { key: "next", label: "Next", hint: "Focus queue" },
  { key: "in_progress", label: "In progress", hint: "Active now" },
  { key: "blocked", label: "Blocked", hint: "Needs intervention" },
  { key: "done", label: "Done", hint: "Completed" },
] as const;

export default function BoardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [title, setTitle] = useState("");
  const [complex, setComplex] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const load = async () => { const [cards, list] = await Promise.all([api.tasks(projectId || undefined), api.projects()]); setTasks(cards); setProjects(list); };
  useEffect(() => { void Promise.all([api.tasks(projectId || undefined), api.projects()]).then(([cards, list]) => { setTasks(cards); setProjects(list); }); }, [projectId]);
  const grouped = useMemo(() => Object.fromEntries(columns.map(column => [column.key, tasks.filter(task => task.status === column.key)])), [tasks]);
  const create = async (event: FormEvent) => { event.preventDefault(); if (!title.trim()) return; setBusy(true); setNotice(""); try { if (complex) { const result=await api.breakdownTask(title.trim(),projectId||undefined); setNotice(`${result.cards.length} cards generated${result.ai_used ? " by AI" : " with the local low-cost planner"}.`); } else await api.createTask({title:title.trim(),project_id:projectId||undefined,status:"backlog",priority:"medium"}); setTitle(""); await load(); } finally { setBusy(false); } };
  const drop = async (event: DragEvent, status: Task["status"]) => { event.preventDefault(); const id=event.dataTransfer.getData("text/task-id"); if (!id) return; setTasks(current=>current.map(task=>task.id===id?{...task,status}:task)); await api.updateTask(id,{status}); await load(); };
  const organize = async () => { setBusy(true); try { const result=await api.organizeTasks(projectId||undefined); setNotice(`${result.organized} cards organized by priority and due date. The Next column is limited to three.`); await load(); } finally { setBusy(false); } };
  const remove = async (id:string) => { await api.deleteTask(id); setTasks(current=>current.filter(task=>task.id!==id)); };
  return <><PageHeader eyebrow="Execution matrix" title="Kanban Board" description="Turn complex outcomes into small cards, then keep only the next few actions in focus." action={<button onClick={()=>void organize()} disabled={busy} className="flex items-center gap-2 rounded-xl border border-cyan/25 bg-cyan/5 px-4 py-2 text-sm text-cyan"><WandSparkles size={15}/> AI organize</button>}/>
    <div className="space-y-6 p-8">
      <form onSubmit={create} className="hud-panel flex flex-wrap items-center gap-3 rounded-2xl p-4"><Bot size={18} className="text-cyan"/><input value={title} onChange={event=>setTitle(event.target.value)} placeholder={complex?"Describe a complex result to break down...":"Add a task card..."} className="min-w-64 flex-1 bg-transparent text-sm outline-none"/><select value={projectId} onChange={event=>setProjectId(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs"><option value="">All projects</option>{projects.map(project=><option key={project.id} value={project.id}>{project.name}</option>)}</select><label className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs ${complex?"border-cyan/30 bg-cyan/10 text-cyan":"hairline text-muted"}`}><input className="hidden" type="checkbox" checked={complex} onChange={event=>setComplex(event.target.checked)}/><Sparkles size={13}/> Break down with AI</label><button disabled={busy||!title.trim()} className="flex items-center gap-2 rounded-lg bg-cyan px-3 py-2 text-xs text-void disabled:opacity-40"><Plus size={14}/>{complex?"Generate cards":"Add card"}</button></form>
      {notice&&<div className="rounded-xl border border-mint/20 bg-mint/5 px-4 py-3 text-xs text-mint">{notice}</div>}
      <div className="grid min-w-[1050px] grid-cols-5 gap-3 overflow-x-auto pb-4">{columns.map(column=><section key={column.key} onDragOver={event=>event.preventDefault()} onDrop={event=>void drop(event,column.key)} className="min-h-[520px] rounded-2xl border hairline bg-black/10 p-3"><div className="flex items-start justify-between border-b hairline px-1 pb-3"><div><h2 className="text-xs uppercase tracking-[.16em] text-white">{column.label}</h2><p className="mt-1 text-[10px] text-muted">{column.hint}</p></div><span className="data-value rounded-full border hairline px-2 py-0.5 text-[10px] text-cyan">{grouped[column.key]?.length??0}</span></div><div className="mt-3 space-y-3">{grouped[column.key]?.map(task=><article draggable onDragStart={event=>{event.dataTransfer.setData("text/task-id",task.id);event.dataTransfer.effectAllowed="move";}} key={task.id} className="group hud-panel cursor-grab rounded-xl p-3 active:cursor-grabbing"><div className="flex gap-2"><GripVertical size={14} className="mt-0.5 shrink-0 text-muted/50"/><div className="min-w-0 flex-1"><div className="mb-2 flex items-center gap-2"><span className={`h-1.5 w-1.5 rounded-full ${task.priority==="critical"?"bg-red-400":task.priority==="high"?"bg-amber-300":task.priority==="low"?"bg-slate-500":"bg-cyan"}`}/><span className="truncate text-[9px] uppercase tracking-wider text-muted">{task.project_name??"Independent"}</span></div><h3 className="text-sm leading-5 text-slate-100">{task.title}</h3>{task.description&&<p className="mt-2 line-clamp-3 text-[11px] leading-5 text-muted">{task.description}</p>}{task.due_at&&<div className="mt-3 flex items-center gap-1 text-[10px] text-amber-200"><CalendarClock size={11}/>{new Date(task.due_at).toLocaleDateString()}</div>}</div><button title="Delete card" onClick={()=>void remove(task.id)} className="self-start p-1 text-muted opacity-0 transition hover:text-red-300 group-hover:opacity-100"><Trash2 size={13}/></button></div></article>)}</div></section>)}</div>
    </div>
  </>;
}
