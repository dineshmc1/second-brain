"use client";

import { Check, Inbox } from "lucide-react";
import { FormEvent, useState } from "react";
import { PopupCloseButton, useClosePopup } from "@/components/popup-close-button";
import { api } from "@/lib/api";

export default function CapturePage() {
  const [text,setText]=useState("");const [saved,setSaved]=useState(false);const close=useClosePopup();
  const submit=async(event:FormEvent)=>{event.preventDefault();if(!text.trim())return;await api.captureInbox(text.trim());setText("");setSaved(true);setTimeout(()=>void close(),650);};
  return <div className="p-3"><form onSubmit={submit} className="hud-panel rounded-2xl p-4 shadow-glow"><div className="flex items-center"><div className="text-[10px] uppercase tracking-[.2em] text-cyan">Smart Inbox // Quick Capture</div><span className="ml-auto text-[9px] text-muted">Esc</span><PopupCloseButton/></div><textarea autoFocus value={text} onChange={event=>setText(event.target.value)} placeholder="Capture an idea, task, question, or observation..." rows={4} className="mt-2 w-full resize-none bg-transparent text-sm outline-none"/><div className="flex items-center border-t hairline pt-3"><span className="text-[10px] text-muted">Route later without breaking focus</span><button className="ml-auto flex items-center gap-2 rounded-xl bg-cyan px-3 py-2 text-xs font-medium text-void">{saved?<Check size={14}/>:<Inbox size={14}/>} {saved?"Captured":"Capture"}</button></div></form></div>;
}
