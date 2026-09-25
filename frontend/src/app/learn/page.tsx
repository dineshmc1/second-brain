"use client";

import { Brain, CheckCircle2, ChevronRight, FlaskConical, Gauge, GraduationCap, Layers3, MessageSquareText, Network, Play, ScanSearch, Sparkles, Users } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { LearningGoal, LearningMode, LearningResult } from "@/types";

const modes: Array<{key:LearningMode;label:string;description:string;prompt:string;icon:typeof Brain}> = [
  {key:"accelerate",label:"Accelerator",description:"Diagnose, teach, retrieve, apply.",prompt:"What do you want to master or practise?",icon:Gauge},
  {key:"explain",label:"Explain for me",description:"Analogy, model, example, checks.",prompt:"What should be explained? Add what confuses you.",icon:Brain},
  {key:"misconception",label:"Misconception Hunter",description:"Find the root of wrong reasoning.",prompt:"Explain the concept in your own words. The system will diagnose it.",icon:ScanSearch},
  {key:"compress",label:"Compression",description:"Reduce volume without losing structure.",prompt:"Paste material or describe what should be compressed.",icon:Layers3},
  {key:"transfer",label:"Knowledge Transfer",description:"Apply one principle across domains.",prompt:"Enter a concept you want to transfer to unfamiliar situations.",icon:Network},
  {key:"simulate",label:"Simulation Lab",description:"Practise judgment inside a scenario.",prompt:"Describe the skill, decision, or situation to simulate.",icon:FlaskConical},
  {key:"experts",label:"Board of Experts",description:"Six lenses, one synthesis.",prompt:"Enter a problem, plan, belief, or decision for the board.",icon:Users},
  {key:"communication",label:"Communication Trainer",description:"Score, coach, and strengthen delivery.",prompt:"Paste what you plan to say or write, and mention the audience.",icon:MessageSquareText},
];

export default function LearnPage() {
  const [goals,setGoals]=useState<LearningGoal[]>([]);
  const [goalTitle,setGoalTitle]=useState("");
  const [objective,setObjective]=useState("");
  const [mode,setMode]=useState<LearningMode>("accelerate");
  const [input,setInput]=useState("");
  const [depth,setDepth]=useState("quick");
  const [result,setResult]=useState<LearningResult>();
  const [busy,setBusy]=useState(false);
  const [usage,setUsage]=useState({calls:0,input_tokens:0,output_tokens:0,cache_hits:0});
  const load=async()=>{const [items,meter]=await Promise.all([api.learningGoals(),api.aiUsage()]);setGoals(items);setUsage(meter);};
  useEffect(()=>{void Promise.all([api.learningGoals(),api.aiUsage(),api.settings()]).then(([items,meter,settings])=>{setGoals(items);setUsage(meter);setDepth(String(settings.ai_depth??"quick"));});},[]);
  const compile=async(event:FormEvent)=>{event.preventDefault();if(!goalTitle.trim()||!objective.trim())return;setBusy(true);try{await api.createLearningGoal(goalTitle.trim(),objective.trim());setGoalTitle("");setObjective("");await load();}finally{setBusy(false);}};
  const run=async(event:FormEvent)=>{event.preventDefault();if(!input.trim())return;setBusy(true);setResult(undefined);try{setResult(await api.runLearning(mode,input.trim(),depth));await load();}finally{setBusy(false);}};
  const master=async(id:string)=>{await api.updateLearningNode(id,{status:"mastered",mastery:100});await load();};
  const selected=modes.find(item=>item.key===mode)!;
  return <><PageHeader eyebrow="Adaptive cognition" title="Learning Lab" description="Build capability through diagnosis, explanation, deliberate practice, transfer, and simulation." action={<div className="text-right"><div className="hud-label">AI economy // Today</div><div className="mt-2 text-xs text-muted">{usage.calls} calls · {usage.input_tokens+usage.output_tokens} tokens · {usage.cache_hits} cache hits</div></div>}/>
    <div className="space-y-6 p-8">
      <section className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <form onSubmit={compile} className="hud-panel rounded-2xl p-5"><div className="flex items-center gap-2"><GraduationCap size={18} className="text-cyan"/><div><div className="hud-label">Goal compiler</div><h2 className="mt-2 text-sm text-white">Outcome → curriculum</h2></div></div><input value={goalTitle} onChange={event=>setGoalTitle(event.target.value)} placeholder="Goal title" className="focus-ring mt-5 w-full rounded-xl border hairline bg-black/20 p-3 text-sm"/><textarea value={objective} onChange={event=>setObjective(event.target.value)} rows={5} placeholder="What should you be able to do—not merely know?" className="focus-ring mt-3 w-full resize-none rounded-xl border hairline bg-black/20 p-3 text-sm leading-6"/><button disabled={busy||!goalTitle.trim()||!objective.trim()} className="mt-3 flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm text-void disabled:opacity-40"><Sparkles size={14}/> Compile curriculum</button><p className="mt-3 text-[10px] leading-5 text-muted">One compact AI call when available; otherwise a local evidence-based curriculum is produced.</p></form>
        <div className="space-y-4">{goals.map(goal=><article key={goal.id} className="hud-panel rounded-2xl p-5"><div className="flex items-start justify-between gap-5"><div><div className="hud-label">Active knowledge path</div><h2 className="mt-2 text-base text-white">{goal.title}</h2><p className="mt-1 text-xs leading-5 text-muted">{goal.objective}</p></div><div className="data-value text-2xl text-cyan">{Math.round(goal.progress)}%</div></div><div className="progress-track mt-4"><div className="progress-fill" style={{width:`${goal.progress}%`}}/></div><div className="mt-5 space-y-2">{goal.nodes.map((node,index)=><div key={node.id} className={`flex items-center gap-3 rounded-xl border p-3 ${node.status==="ready"||node.status==="learning"?"border-cyan/30 bg-cyan/[.04]":"hairline bg-black/10"}`}><span className="data-value grid h-6 w-6 place-items-center rounded-full border hairline text-[10px] text-cyan">{index+1}</span><div className="min-w-0 flex-1"><div className="text-sm text-white">{node.title}</div><div className="mt-1 truncate text-[10px] text-muted">{node.description}</div></div>{node.status==="mastered"?<CheckCircle2 size={16} className="text-mint"/>:<button disabled={node.status==="locked"} onClick={()=>void master(node.id)} title="Mark mastered" className="rounded-lg border hairline p-1.5 text-muted hover:text-mint disabled:opacity-20"><ChevronRight size={13}/></button>}</div>)}</div></article>)}{!goals.length&&<div className="grid min-h-64 place-items-center rounded-2xl border border-dashed hairline text-center"><div><Network size={28} className="mx-auto text-cyan/50"/><h2 className="mt-3 text-white">No knowledge paths yet</h2><p className="mt-1 text-sm text-muted">Describe a real capability you want to build.</p></div></div>}</div>
      </section>
      <section className="hud-panel rounded-2xl p-5"><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{modes.map(item=><button key={item.key} onClick={()=>{setMode(item.key);setResult(undefined);}} className={`rounded-xl border p-3 text-left transition ${mode===item.key?"border-cyan/35 bg-cyan/10":"hairline bg-black/10 hover:bg-white/[.025]"}`}><item.icon size={16} className={mode===item.key?"text-cyan":"text-muted"}/><div className="mt-2 text-xs text-white">{item.label}</div><div className="mt-1 text-[10px] leading-4 text-muted">{item.description}</div></button>)}</div>
        <form onSubmit={run} className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr]"><div><div className="flex items-center justify-between"><div><div className="hud-label">{selected.label}</div><h2 className="mt-2 text-base text-white">Cognitive workbench</h2></div><select value={depth} onChange={event=>setDepth(event.target.value)} className="rounded-lg border hairline bg-panel px-3 py-2 text-xs"><option value="quick">Quick · lowest cost</option><option value="standard">Standard</option><option value="deep">Deep</option></select></div><textarea value={input} onChange={event=>setInput(event.target.value)} rows={12} placeholder={selected.prompt} className="focus-ring mt-4 w-full resize-none rounded-xl border hairline bg-black/20 p-4 text-sm leading-6"/><button disabled={busy||!input.trim()} className="mt-3 flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm text-void disabled:opacity-40"><Play size={14}/>{busy?"Thinking...":"Run session"}</button></div><div className="min-h-80 rounded-xl border hairline bg-black/20 p-5">{result?<><div className="mb-4 flex items-center gap-2 text-[9px] uppercase tracking-widest text-cyan">{result.local?"Local reasoning":"OpenRouter"}{result.cache_hit&&" · Cached"}{!result.local&&!result.cache_hit&&` · ${result.input_tokens+result.output_tokens} tokens`}</div><div className="prose prose-invert prose-sm max-w-none text-sm leading-7 text-slate-200"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result.result}</ReactMarkdown></div></>:<div className="grid h-full place-items-center text-center"><div><selected.icon size={28} className="mx-auto text-cyan/35"/><p className="mt-3 text-sm text-muted">Your session output will appear here.</p></div></div>}</div></form>
      </section>
    </div>
  </>;
}
