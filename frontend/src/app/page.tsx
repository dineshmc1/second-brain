import { ChatView } from "@/components/chat-view";

export default function Home() {
  return <div className="relative grid min-h-screen place-items-center overflow-hidden px-6"><div className="pointer-events-none absolute left-1/2 top-1/2 h-[620px] w-[620px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan/[.035]"/><div className="pointer-events-none absolute left-1/2 top-1/2 h-[450px] w-[450px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan/[.05]"/><div className="z-10 w-full"><div className="mb-8 text-center text-[10px] uppercase tracking-[.38em] text-muted">Second Brain / Local Core</div><ChatView compact/></div></div>;
}

