"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clock, Pencil, Plus, Search, Star, Trash2, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { Memory, Project } from "@/types";

const memoryTypes = ["semantic", "personal", "episodic", "decision", "project", "task", "people", "conversation"];
type EditDraft = { title: string; content: string; memory_type: string; category: string; tags: string; project_id: string };

export default function MemoryPage() {
  const [items, setItems] = useState<Memory[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("current");
  const [note, setNote] = useState("");
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<Memory | null>(null);
  const [draft, setDraft] = useState<EditDraft>({ title: "", content: "", memory_type: "semantic", category: "", tags: "", project_id: "" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => api.memories(status, type).then(setItems), [status, type]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { void api.projects().then(setProjects); }, []);
  const filtered = useMemo(() => items.filter(item => `${item.title} ${item.normalized_fact} ${item.tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [items, query]);
  const add = async (event: FormEvent) => { event.preventDefault(); if (!note.trim()) return; await api.createMemory(note); setNote(""); setAdding(false); await load(); };
  const remove = async (id: string) => { if (!confirm("Move this memory to deleted history?")) return; await api.deleteMemory(id); await load(); };
  const important = async (item: Memory) => { await api.updateMemory(item.id, { importance_score: item.importance_score > .8 ? .6 : .95 }); await load(); };
  const openEditor = (item: Memory) => {
    setEditing(item);
    setDraft({ title: item.title, content: item.normalized_fact, memory_type: item.memory_type, category: item.category ?? "", tags: item.tags.join(", "), project_id: item.project_id ?? "" });
  };
  const saveEdit = async (event: FormEvent) => {
    event.preventDefault();
    if (!editing || !draft.title.trim() || !draft.content.trim()) return;
    setSaving(true);
    try {
      await api.updateMemory(editing.id, {
        title: draft.title.trim(),
        content: draft.content.trim(),
        memory_type: draft.memory_type,
        category: draft.category.trim() || null,
        tags: draft.tags.split(",").map(tag => tag.trim()).filter(Boolean),
        project_id: draft.project_id || null,
      });
      setEditing(null);
      await load();
    } finally { setSaving(false); }
  };
  const setField = (field: keyof EditDraft, value: string) => setDraft(current => ({ ...current, [field]: value }));

  return <><PageHeader eyebrow="Knowledge vault" title="Memory" description="Search, inspect, edit, and organize durable knowledge." action={<button onClick={() => setAdding(true)} className="flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void"><Plus size={16}/> Add memory</button>}/>
    <section className="p-8">
      <div className="glass mb-6 flex flex-wrap items-center gap-3 rounded-2xl p-3"><div className="flex min-w-[260px] flex-1 items-center gap-2 px-2 text-muted"><Search size={16}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search memories…" className="w-full bg-transparent py-2 text-sm text-white outline-none"/></div>
        <select value={type} onChange={event => setType(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs text-muted"><option value="">All types</option>{memoryTypes.map(value => <option key={value}>{value}</option>)}</select>
        <select value={status} onChange={event => setStatus(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs text-muted"><option value="current">Current</option><option value="all">Current + history</option><option value="superseded">Superseded</option></select>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map(item => <motion.article layout key={item.id} className="glass group rounded-2xl p-5 transition hover:border-cyan/25">
        <div className="flex items-start justify-between"><span className="rounded-full border border-cyan/15 bg-cyan/5 px-2 py-1 text-[9px] uppercase tracking-[.16em] text-cyan">{item.memory_type}</span><div className="flex opacity-60 transition group-hover:opacity-100"><button onClick={() => openEditor(item)} className="p-1.5 text-muted hover:text-cyan" aria-label="Edit memory"><Pencil size={15}/></button><button onClick={() => void important(item)} className="p-1.5 text-muted hover:text-amber-300" aria-label="Toggle importance"><Star size={15} fill={item.importance_score > .8 ? "currentColor" : "none"}/></button><button onClick={() => void remove(item.id)} className="p-1.5 text-muted hover:text-red-300" aria-label="Delete memory"><Trash2 size={15}/></button></div></div>
        <button onClick={() => openEditor(item)} className="block w-full text-left"><h2 className="mt-4 text-base text-white">{item.title}</h2><p className="mt-2 text-sm leading-6 text-slate-300">{item.normalized_fact}</p></button>
        <div className="mt-5 flex flex-wrap gap-1.5">{item.tags.map(tag => <span key={tag} className="text-[10px] text-muted">#{tag}</span>)}</div>
        <div className="mt-4 flex items-center gap-2 border-t hairline pt-3 text-[10px] text-muted"><Clock size={12}/>{new Date(item.updated_at).toLocaleDateString()}<span className="ml-auto capitalize">{item.status}</span></div>
      </motion.article>)}</div>
      {!filtered.length && <div className="py-24 text-center text-sm text-muted">No memories match these filters.</div>}
    </section>

    <AnimatePresence>{adding && <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-6 backdrop-blur-sm"><motion.form initial={{scale:.97,y:10}} animate={{scale:1,y:0}} onSubmit={add} className="glass w-full max-w-xl rounded-2xl p-6"><div className="flex items-center"><h2 className="text-lg">Add knowledge</h2><button type="button" onClick={() => setAdding(false)} className="ml-auto p-2 text-muted"><X size={18}/></button></div><p className="mt-1 text-xs text-muted">Write naturally. The app will classify and connect it.</p><textarea autoFocus value={note} onChange={event => setNote(event.target.value)} rows={7} className="focus-ring mt-5 w-full resize-none rounded-xl border hairline bg-black/20 p-4 text-sm" placeholder="Remember that…"/><div className="mt-4 flex justify-end gap-2"><button type="button" onClick={() => setAdding(false)} className="rounded-xl px-4 py-2 text-sm text-muted">Cancel</button><button className="rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void">Save memory</button></div></motion.form></motion.div>}</AnimatePresence>

    <AnimatePresence>{editing && <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-6 backdrop-blur-sm"><motion.form initial={{scale:.97,y:10}} animate={{scale:1,y:0}} onSubmit={saveEdit} className="glass max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl p-6"><div className="flex items-center"><div><h2 className="text-lg">Edit memory</h2><p className="mt-1 text-xs text-muted">The previous value is retained in version history.</p></div><button type="button" onClick={() => setEditing(null)} className="ml-auto p-2 text-muted"><X size={18}/></button></div>
      <label className="mt-5 block text-xs text-muted">Title</label><input autoFocus value={draft.title} onChange={event => setField("title", event.target.value)} className="focus-ring mt-2 w-full rounded-xl border hairline bg-black/20 p-3 text-sm"/>
      <label className="mt-4 block text-xs text-muted">Memory</label><textarea value={draft.content} onChange={event => setField("content", event.target.value)} rows={6} className="focus-ring mt-2 w-full resize-y rounded-xl border hairline bg-black/20 p-3 text-sm"/>
      <div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="text-xs text-muted">Type<select value={draft.memory_type} onChange={event => setField("memory_type", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-panel p-3 text-sm text-white">{memoryTypes.map(value => <option key={value}>{value}</option>)}</select></label><label className="text-xs text-muted">Project<select value={draft.project_id} onChange={event => setField("project_id", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-panel p-3 text-sm text-white"><option value="">No project</option>{projects.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label></div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="text-xs text-muted">Category<input value={draft.category} onChange={event => setField("category", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-black/20 p-3 text-sm text-white"/></label><label className="text-xs text-muted">Tags, comma separated<input value={draft.tags} onChange={event => setField("tags", event.target.value)} className="mt-2 w-full rounded-xl border hairline bg-black/20 p-3 text-sm text-white"/></label></div>
      <div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setEditing(null)} className="rounded-xl px-4 py-2 text-sm text-muted">Cancel</button><button disabled={saving} className="rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void disabled:opacity-50">{saving ? "Saving…" : "Save changes"}</button></div>
    </motion.form></motion.div>}</AnimatePresence>
  </>;
}
