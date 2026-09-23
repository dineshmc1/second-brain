"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clock, Pencil, Plus, Search, Star, Trash2, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { Memory } from "@/types";

export default function MemoryPage() {
  const [items, setItems] = useState<Memory[]>([]); const [query, setQuery] = useState("");
  const [type, setType] = useState(""); const [status, setStatus] = useState("current"); const [note, setNote] = useState(""); const [adding, setAdding] = useState(false);
  const load = () => api.memories(status, type).then(setItems);
  useEffect(() => { void load(); }, [status, type]);
  const filtered = useMemo(() => items.filter(item => `${item.title} ${item.normalized_fact} ${item.tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [items, query]);
  const add = async (event: FormEvent) => { event.preventDefault(); if (!note.trim()) return; await api.createMemory(note); setNote(""); setAdding(false); load(); };
  const remove = async (id: string) => { if (!confirm("Move this memory to deleted history?")) return; await api.deleteMemory(id); load(); };
  const important = async (item: Memory) => { await api.updateMemory(item.id, { importance_score: item.importance_score > .8 ? .6 : .95 }); load(); };
  return <><PageHeader eyebrow="Knowledge vault" title="Memory" description="Search, inspect, and manage durable knowledge." action={<button onClick={() => setAdding(true)} className="flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void"><Plus size={16}/> Add memory</button>}/>
    <section className="p-8">
      <div className="glass mb-6 flex flex-wrap items-center gap-3 rounded-2xl p-3"><div className="flex min-w-[260px] flex-1 items-center gap-2 px-2 text-muted"><Search size={16}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search memories…" className="w-full bg-transparent py-2 text-sm text-white outline-none"/></div>
        <select value={type} onChange={event => setType(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs text-muted"><option value="">All types</option>{["semantic","personal","episodic","decision","project","task","people","conversation"].map(value => <option key={value}>{value}</option>)}</select>
        <select value={status} onChange={event => setStatus(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs text-muted"><option value="current">Current</option><option value="all">Current + history</option><option value="superseded">Superseded</option></select>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map(item => <motion.article layout key={item.id} className="glass group rounded-2xl p-5 transition hover:border-cyan/25">
        <div className="flex items-start justify-between"><span className="rounded-full border border-cyan/15 bg-cyan/5 px-2 py-1 text-[9px] uppercase tracking-[.16em] text-cyan">{item.memory_type}</span><div className="flex opacity-0 transition group-hover:opacity-100"><button onClick={() => important(item)} className="p-1.5 text-muted hover:text-amber-300"><Star size={15} fill={item.importance_score > .8 ? "currentColor" : "none"}/></button><button onClick={() => remove(item.id)} className="p-1.5 text-muted hover:text-red-300"><Trash2 size={15}/></button></div></div>
        <h2 className="mt-4 text-base text-white">{item.title}</h2><p className="mt-2 text-sm leading-6 text-slate-300">{item.normalized_fact}</p>
        <div className="mt-5 flex flex-wrap gap-1.5">{item.tags.map(tag => <span key={tag} className="text-[10px] text-muted">#{tag}</span>)}</div>
        <div className="mt-4 flex items-center gap-2 border-t hairline pt-3 text-[10px] text-muted"><Clock size={12}/>{new Date(item.created_at).toLocaleDateString()}<span className="ml-auto capitalize">{item.status}</span></div>
      </motion.article>)}</div>
      {!filtered.length && <div className="py-24 text-center text-sm text-muted">No memories match these filters.</div>}
    </section>
    <AnimatePresence>{adding && <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-6 backdrop-blur-sm"><motion.form initial={{scale:.97,y:10}} animate={{scale:1,y:0}} onSubmit={add} className="glass w-full max-w-xl rounded-2xl p-6"><div className="flex items-center"><h2 className="text-lg">Add knowledge</h2><button type="button" onClick={() => setAdding(false)} className="ml-auto p-2 text-muted"><X size={18}/></button></div><p className="mt-1 text-xs text-muted">Write naturally. The app will classify and connect it.</p><textarea autoFocus value={note} onChange={event => setNote(event.target.value)} rows={7} className="focus-ring mt-5 w-full resize-none rounded-xl border hairline bg-black/20 p-4 text-sm" placeholder="Remember that…"/><div className="mt-4 flex justify-end gap-2"><button type="button" onClick={() => setAdding(false)} className="rounded-xl px-4 py-2 text-sm text-muted">Cancel</button><button className="rounded-xl bg-cyan px-4 py-2 text-sm font-medium text-void">Save memory</button></div></motion.form></motion.div>}</AnimatePresence>
  </>;
}
