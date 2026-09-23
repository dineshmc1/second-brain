"use client";

import { Search, Send } from "lucide-react";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function QuickPage() {
  const [query, setQuery] = useState(""); const [answer, setAnswer] = useState(""); const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!query.trim()) return; setBusy(true); try { setAnswer((await api.chat(query)).answer); } finally { setBusy(false); } };
  return <div className="p-3"><form onSubmit={submit} className="glass rounded-2xl p-3 shadow-glow"><div className="flex items-center gap-3"><Search size={18} className="text-cyan"/><input autoFocus value={query} onChange={e => setQuery(e.target.value)} placeholder="Ask your Second Brain…" className="flex-1 bg-transparent py-2 text-sm outline-none"/><button disabled={busy} className="rounded-lg bg-cyan p-2 text-void"><Send size={15}/></button></div>{answer && <div className="mt-3 border-t hairline px-1 pt-3 text-sm leading-6 text-slate-200">{answer}</div>}</form></div>;
}

