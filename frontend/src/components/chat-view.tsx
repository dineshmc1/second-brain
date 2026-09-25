"use client";

import { motion } from "framer-motion";
import { Bot, User, Volume2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "@/lib/api";
import type { Citation } from "@/types";
import { ChatComposer } from "./chat-composer";
import { Orb } from "./orb";

type Message = { role: "user" | "assistant"; content: string; citations?: Citation[]; offline?: boolean };
type ResponseMode = "text" | "voice" | "both";

export function ChatView({ compact = false, projectId }: { compact?: boolean; projectId?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [responseMode, setResponseMode] = useState<ResponseMode>("text");
  const [autoRead, setAutoRead] = useState(false);
  const audio = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    void api.settings().then(settings => {
      const configured = String(settings.response_mode ?? "text");
      setResponseMode(configured === "voice" || configured === "both" ? configured : "text");
      setAutoRead(Boolean(settings.auto_read));
    });
  }, []);
  useEffect(() => { setConversationId(undefined); setMessages([]); }, [projectId]);
  useEffect(() => () => {
    window.speechSynthesis?.cancel();
    audio.current?.pause();
  }, []);

  const playVoice = useCallback(async (text: string) => {
    setVoiceError("");
    try {
      if ("speechSynthesis" in window && "SpeechSynthesisUtterance" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1;
        utterance.onstart = () => setSpeaking(true);
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => { setSpeaking(false); setVoiceError("Windows voice playback failed. Check the installed speech voices."); };
        window.speechSynthesis.speak(utterance);
        return;
      }
      const blob = await api.speak(text);
      const url = URL.createObjectURL(blob);
      const player = new Audio(url);
      audio.current = player;
      player.onplay = () => setSpeaking(true);
      player.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      player.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); setVoiceError("Voice playback failed."); };
      await player.play();
    } catch (error) {
      setSpeaking(false);
      setVoiceError(error instanceof Error ? error.message : "Voice playback failed.");
    }
  }, []);

  const send = async (content: string) => {
    setMessages(items => [...items, { role: "user", content }]); setBusy(true); setVoiceError("");
    try {
      const result = await api.chat(content, conversationId, responseMode, projectId);
      setConversationId(result.conversation_id);
      setMessages(items => [...items, { role: "assistant", content: result.answer, citations: result.citations, offline: result.offline }]);
      if (responseMode === "voice" || responseMode === "both" || autoRead) await playVoice(result.answer);
    } catch (error) { setMessages(items => [...items, { role: "assistant", content: error instanceof Error ? error.message : "Something went wrong." }]); }
    finally { setBusy(false); }
  };

  if (!messages.length && compact) return <div className="flex flex-col items-center gap-8"><Orb state={busy ? "thinking" : speaking ? "speaking" : "idle"}/><div className="text-center"><h1 className="text-3xl font-light tracking-tight text-gradient">What do you need?</h1><p className="mt-2 text-sm text-muted">Ask, remember, or find anything you have saved.</p></div><ChatComposer onSend={send} busy={busy} large/>{voiceError && <p className="text-xs text-red-200">{voiceError}</p>}</div>;
  return <div className="mx-auto flex h-[calc(100vh-5rem)] max-w-4xl flex-col px-6">
    <div className="flex-1 space-y-7 overflow-y-auto py-8">
      {!messages.length && <div className="grid h-full place-items-center"><div className="text-center"><Orb state={speaking ? "speaking" : "idle"}/><h2 className="mt-4 text-xl text-white">Start a conversation</h2><p className="mt-2 text-sm text-muted">Your stored knowledge will be searched first.</p></div></div>}
      {messages.map((message, index) => <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} key={index} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
        {message.role === "assistant" && <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-cyan/30 text-cyan"><Bot size={15}/></div>}
        <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-cyan/10 text-white" : "glass"}`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          {message.role === "assistant" && <button type="button" onClick={() => void playVoice(message.content)} className="mt-2 flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-cyan hover:text-white"><Volume2 size={13}/> Read aloud</button>}
          {!!message.citations?.length && <div className="mt-4 flex flex-wrap gap-2 border-t hairline pt-3">{message.citations.map(citation => <button key={citation.id} title={citation.excerpt} className="rounded-full border hairline bg-white/[.025] px-2.5 py-1 text-[10px] text-cyan hover:bg-cyan/10">{citation.label}</button>)}</div>}
          {message.offline && <div className="mt-2 text-[10px] uppercase tracking-widest text-amber-300">Local answer</div>}
        </div>
        {message.role === "user" && <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white/5 text-muted"><User size={15}/></div>}
      </motion.div>)}
      {busy && <div className="flex items-center gap-3 text-xs text-muted"><Orb state="thinking" size={36}/>Searching your Second Brain…</div>}
    </div>
    <div className="pb-5"><ChatComposer onSend={send} busy={busy}/>{speaking && <p className="mt-2 text-center text-[10px] uppercase tracking-widest text-cyan">Speaking response…</p>}{voiceError && <p className="mt-2 text-center text-xs text-red-200">{voiceError}</p>}<p className="mt-2 text-center text-[10px] text-muted/60">Answers use local evidence first. Verify important details in the cited source.</p></div>
  </div>;
}
