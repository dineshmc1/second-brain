"use client";

import { Loader2, Mic, Paperclip, Send, Square } from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

export function ChatComposer({ onSend, busy, large = false }: { onSend: (message: string) => void; busy: boolean; large?: boolean }) {
  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => () => {
    if (stopTimer.current) clearTimeout(stopTimer.current);
    if (recorder.current?.state === "recording") recorder.current.stop();
    stream.current?.getTracks().forEach(track => track.stop());
  }, []);

  const submit = (event?: FormEvent) => { event?.preventDefault(); const message = value.trim(); if (!message || busy) return; onSend(message); setValue(""); };
  const key = (event: KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } };
  const toggleRecording = async () => {
    if (recording) { recorder.current?.stop(); return; }
    setVoiceError("");
    if (!navigator.mediaDevices?.getUserMedia) { setVoiceError("Microphone capture is not available on this device."); return; }
    try {
      const microphone = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      stream.current = microphone;
      const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"].find(type => MediaRecorder.isTypeSupported(type));
      const next = new MediaRecorder(microphone, preferred ? { mimeType: preferred } : undefined);
      chunks.current = [];
      next.ondataavailable = event => { if (event.data.size) chunks.current.push(event.data); };
      next.onerror = () => setVoiceError("Microphone recording failed. Check Windows microphone permissions.");
      next.onstop = async () => {
        if (stopTimer.current) clearTimeout(stopTimer.current);
        microphone.getTracks().forEach(track => track.stop());
        setRecording(false);
        setTranscribing(true);
        try {
          const audio = new Blob(chunks.current, { type: next.mimeType || "audio/webm" });
          if (!audio.size) throw new Error("No audio was recorded. Check the selected microphone.");
          const result = await api.transcribe(audio);
          setValue(current => [current.trim(), result.transcript].filter(Boolean).join(" "));
        } catch (error) {
          setVoiceError(error instanceof Error ? error.message : "Speech recognition failed.");
        } finally { setTranscribing(false); }
      };
      next.start(250);
      recorder.current = next;
      setRecording(true);
      stopTimer.current = setTimeout(() => { if (next.state === "recording") next.stop(); }, 30_000);
    } catch (error) {
      setVoiceError(error instanceof Error && error.name === "NotAllowedError" ? "Microphone permission was denied. Enable it in Windows Settings → Privacy & security → Microphone." : "Could not open the microphone.");
    }
  };
  const upload = async (files: FileList | null) => { if (!files?.length) return; const result = await api.upload(files[0]); setValue(`Ask about ${result.filename}`); };

  return <form onSubmit={submit} className={`glass rounded-2xl p-2 shadow-glow ${large ? "w-full max-w-2xl" : "w-full"}`}>
    <textarea aria-label="Ask your Second Brain" value={value} onChange={event => setValue(event.target.value)} onKeyDown={key} rows={large ? 2 : 1} placeholder="Ask your Second Brain…" className="focus-ring max-h-40 w-full resize-none bg-transparent px-3 py-3 text-sm text-white placeholder:text-muted/70"/>
    <div className="flex items-center gap-1 border-t hairline pt-2">
      <input ref={fileInput} hidden type="file" accept=".pdf,.txt,.md,.docx,image/*" onChange={event => void upload(event.target.files)}/>
      <button type="button" onClick={() => fileInput.current?.click()} className="rounded-lg p-2.5 text-muted hover:bg-white/5 hover:text-cyan" aria-label="Add file"><Paperclip size={17}/></button>
      <button type="button" disabled={transcribing} onClick={() => void toggleRecording()} className={`rounded-lg p-2.5 disabled:opacity-40 ${recording ? "bg-red-400/10 text-red-300" : "text-muted hover:bg-white/5 hover:text-cyan"}`} aria-label={recording ? "Stop recording" : "Speak"}>{transcribing ? <Loader2 size={16} className="animate-spin"/> : recording ? <Square size={16}/> : <Mic size={17}/>}</button>
      <span className="ml-1 text-[10px] uppercase tracking-[.14em] text-muted">{recording ? "Listening — click stop" : transcribing ? "Transcribing locally…" : "Voice input"}</span>
      <button disabled={busy || transcribing || !value.trim()} className="ml-auto grid h-9 w-9 place-items-center rounded-xl bg-cyan text-void transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-30" aria-label="Send"><Send size={16}/></button>
    </div>
    {voiceError && <div className="px-3 pb-2 pt-1 text-xs leading-5 text-red-200">{voiceError}</div>}
  </form>;
}
