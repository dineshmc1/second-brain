"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { Memory } from "@/types";

export default function TimelinePage() {
  const [items, setItems] = useState<Memory[]>([]); useEffect(() => { api.memories("all").then(setItems); }, []);
  const groups = items.reduce<Record<string, Memory[]>>((result, item) => { const month = new Date(item.created_at).toLocaleDateString(undefined, { month: "long", year: "numeric" }); (result[month] ??= []).push(item); return result; }, {});
  return <><PageHeader eyebrow="Temporal memory" title="Timeline" description="See what changed, and when."/><div className="mx-auto max-w-4xl p-8">{Object.entries(groups).map(([month, memories]) => <section key={month} className="mb-10"><h2 className="mb-5 text-xs uppercase tracking-[.2em] text-cyan">{month}</h2><div className="border-l border-cyan/15 pl-6">{memories.map(memory => <article key={memory.id} className="relative mb-3 rounded-xl border hairline bg-white/[.02] p-4 before:absolute before:-left-[29px] before:top-5 before:h-1.5 before:w-1.5 before:rounded-full before:bg-cyan"><div className="text-xs text-muted">{new Date(memory.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short" })} · {memory.status}</div><div className="mt-1 text-sm text-white">{memory.normalized_fact}</div></article>)}</div></section>)}</div></>;
}

