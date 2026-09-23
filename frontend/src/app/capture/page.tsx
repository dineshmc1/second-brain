"use client";

import { Check, Mic, Save } from "lucide-react";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function CapturePage() {
  const [text, setText] = useState(""); const [saved, setSaved] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!text.trim()) return; await api.createMemory(text); setText(""); setSaved(true); setTimeout(() => setSaved(false), 1500); };
  return <div className="p-3"><form onSubmit={submit} className="glass rounded-2xl p-4 shadow-glow"><div className="text-[10px] uppercase tracking-[.2em] text-cyan">Quick Capture</div><textarea autoFocus value={text} onChange={e => setText(e.target.value)} placeholder="Type something worth remembering…" rows={4} className="mt-3 w-full resize-none bg-transparent text-sm outline-none"/><div className="flex items-center border-t hairline pt-3"><span className="text-[10px] text-muted">Auto-detect type</span><button className="ml-auto flex items-center gap-2 rounded-xl bg-cyan px-3 py-2 text-xs font-medium text-void">{saved ? <Check size={14}/> : <Save size={14}/>} {saved ? "Saved" : "Remember"}</button></div></form></div>;
}

