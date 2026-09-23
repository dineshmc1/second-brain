"use client";

import { Mic, Paperclip, Send, Square } from "lucide-react";
import { FormEvent, KeyboardEvent, useRef, useState } from "react";
import { api } from "@/lib/api";

export function ChatComposer({ onSend, busy, large = false }: { onSend: (message: string) => void; busy: boolean; large?: boolean }) {
  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const submit = (event?: FormEvent) => { event?.preventDefault(); const message = value.trim(); if (!message || busy) return; onSend(message); setValue(""); };
  const key = (event: KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } };
  const toggleRecording = async () => {
    if (recording) { recorder.current?.stop(); setRecording(false); return; }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const next = new MediaRecorder(stream); chunks.current = [];
    next.ondataavailable = (event) => chunks.current.push(event.data);
    next.onstop = async () => { stream.getTracks().forEach(track => track.stop()); const result = await api.transcribe(new Blob(chunks.current, { type: next.mimeType })); setValue(result.transcript); };
    next.start(); recorder.current = next; setRecording(true);
  };
  const upload = async (files: FileList | null) => { if (!files?.length) return; const result = await api.upload(files[0]); setValue(`Ask about ${result.filename}`); };
  return <form onSubmit={submit} className={`glass rounded-2xl p-2 shadow-glow ${large ? "w-full max-w-2xl" : "w-full"}`}>
    <textarea aria-label="Ask your Second Brain" value={value} onChange={event => setValue(event.target.value)} onKeyDown={key} rows={large ? 2 : 1} placeholder="Ask your Second Brain…" className="focus-ring max-h-40 w-full resize-none bg-transparent px-3 py-3 text-sm text-white placeholder:text-muted/70"/>
    <div className="flex items-center gap-1 border-t hairline pt-2">
      <input ref={fileInput} hidden type="file" accept=".pdf,.txt,.md,.docx,image/*" onChange={event => upload(event.target.files)}/>
      <button type="button" onClick={() => fileInput.current?.click()} className="rounded-lg p-2.5 text-muted hover:bg-white/5 hover:text-cyan" aria-label="Add file"><Paperclip size={17}/></button>
      <button type="button" onClick={toggleRecording} className={`rounded-lg p-2.5 ${recording ? "bg-red-400/10 text-red-300" : "text-muted hover:bg-white/5 hover:text-cyan"}`} aria-label={recording ? "Stop recording" : "Speak"}>{recording ? <Square size={16}/> : <Mic size={17}/>}</button>
      <span className="ml-1 text-[10px] uppercase tracking-[.14em] text-muted">{recording ? "Listening" : "Local capture"}</span>
      <button disabled={busy || !value.trim()} className="ml-auto grid h-9 w-9 place-items-center rounded-xl bg-cyan text-void transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-30" aria-label="Send"><Send size={16}/></button>
    </div>
  </form>;
}

