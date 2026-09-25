"use client";

import { Brain, FileText, Search, Send, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { ChatResponse, SearchResult } from "@/types";

export default function SearchPage(){
  const [query,setQuery]=useState("");const [results,setResults]=useState<SearchResult[]>([]);const [answer,setAnswer]=useState<ChatResponse>();const [busy,setBusy]=useState(false);
  const search=async(event:FormEvent)=>{event.preventDefault();if(!query.trim())return;setBusy(true);setAnswer(undefined);try{setResults(await api.search(query.trim()));}finally{setBusy(false);}};
  const ask=async()=>{if(!query.trim())return;setBusy(true);try{setAnswer(await api.chat(query.trim()));}finally{setBusy(false);}};
  return <><PageHeader eyebrow="Semantic retrieval" title="Natural Language Search" description="Search by meaning, then ask for a source-backed synthesis when raw results are not enough."/>
    <div className="space-y-6 p-8"><form onSubmit={search} className="hud-panel flex items-center gap-3 rounded-2xl p-4"><Search size={19} className="text-cyan"/><input autoFocus value={query} onChange={event=>setQuery(event.target.value)} placeholder="What did I decide about pricing? Which ideas relate to feedback loops?" className="flex-1 bg-transparent text-sm outline-none"/><button disabled={busy||!query.trim()} className="rounded-xl border border-cyan/25 px-4 py-2 text-xs text-cyan">Find evidence</button><button type="button" onClick={()=>void ask()} disabled={busy||!query.trim()} className="flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-xs text-void"><Sparkles size={13}/> Answer with sources</button></form>
      {answer&&<section className="hud-panel rounded-2xl p-6"><div className="flex items-center gap-2"><Brain size={17} className="text-cyan"/><span className="hud-label">Grounded synthesis // {Math.round(answer.confidence*100)}% confidence</span></div><div className="prose prose-invert prose-sm mt-5 max-w-none text-sm leading-7 text-slate-200"><ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.answer}</ReactMarkdown></div><div className="mt-5 border-t hairline pt-4"><div className="hud-label">Evidence trail</div><div className="mt-3 grid gap-2 md:grid-cols-2">{answer.citations.map(citation=><article key={citation.id} title={citation.excerpt} className="rounded-xl border hairline bg-black/15 p-3"><div className="flex items-center gap-2 text-xs text-cyan"><FileText size={12}/>{citation.label}</div><p className="mt-2 line-clamp-2 text-[10px] leading-4 text-muted">{citation.excerpt}</p></article>)}</div></div></section>}
      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{results.map(result=><article key={`${result.kind}-${result.id}`} className="hud-panel rounded-2xl p-5"><div className="flex items-center justify-between"><span className="rounded-full border border-cyan/15 px-2 py-1 text-[9px] uppercase tracking-wider text-cyan">{result.kind}</span><span className="data-value text-[10px] text-muted">{result.score.toFixed(3)}</span></div><h2 className="mt-3 text-sm text-white">{result.title}</h2><p className="mt-2 line-clamp-5 text-xs leading-5 text-muted">{result.excerpt}</p></article>)}{!results.length&&!answer&&<div className="col-span-full grid min-h-72 place-items-center rounded-2xl border border-dashed hairline"><div className="text-center"><Send size={26} className="mx-auto text-cyan/40"/><p className="mt-3 text-sm text-muted">Ask naturally. Exact keywords are optional.</p></div></div>}</section>
    </div>
  </>;
}
