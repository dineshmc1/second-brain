"use client";

import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, ChevronLeft, Columns3, Files, FolderKanban, Gauge, GraduationCap, Home, Inbox, Menu, MessageSquare, Search, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { api } from "@/lib/api";

const navigation = [
  ["Command", "/", Home], ["Smart Inbox", "/inbox", Inbox], ["Kanban", "/board", Columns3],
  ["Projects", "/projects", FolderKanban], ["Learning Lab", "/learn", GraduationCap],
  ["Intelligence", "/intelligence", Gauge], ["Search", "/search", Search],
  ["Ask Brain", "/chat", MessageSquare], ["Memory", "/memory", BrainCircuit], ["Sources", "/files", Files],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mode, setMode] = useState("checking");
  useEffect(() => { api.health().then((health) => setMode(health.mode)).catch(() => setMode("offline")); }, []);
  if (path.startsWith("/quick") || path.startsWith("/capture")) return <main className="min-h-screen">{children}</main>;
  return <div className="flex min-h-screen">
    <div className="scan-beam" aria-hidden="true"/>
    <motion.aside animate={{ width: collapsed ? 76 : 244 }} className="glass fixed inset-y-0 left-0 z-30 flex flex-col border-y-0 border-l-0 border-r-cyan/15">
      <div className="flex h-20 items-center gap-3 px-5">
        <div className="hud-orbit relative grid h-10 w-10 shrink-0 place-items-center rounded-full border border-cyan/40 bg-cyan/5 text-cyan shadow-glow"><BrainCircuit size={19}/></div>
        <AnimatePresence>{!collapsed && <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="overflow-hidden whitespace-nowrap">
          <div className="text-sm font-semibold tracking-[.2em] text-gradient">SECOND BRAIN</div><div className="text-[9px] uppercase tracking-[.26em] text-muted">Cognitive OS // Online</div>
        </motion.div>}</AnimatePresence>
      </div>
      <nav className="mt-2 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
        {navigation.map(([label, href, Icon]) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return <Link key={href} href={href} title={collapsed ? label : undefined} className={`group relative flex h-10 items-center gap-3 rounded-lg px-3 text-sm transition ${active ? "border border-cyan/20 bg-cyan/10 text-cyan shadow-[inset_0_0_24px_rgba(104,232,255,.04)]" : "border border-transparent text-muted hover:bg-white/[.04] hover:text-white"}`}>
            <Icon size={18} className="shrink-0"/>{!collapsed && <span className="whitespace-nowrap">{label}</span>}
            {active && <motion.span layoutId="nav" className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_12px_#68e8ff]"/>}
          </Link>;
        })}
      </nav>
      <div className="space-y-3 p-3">
        {!collapsed && <Link href="/settings" className="flex w-full items-center gap-2 rounded-xl border hairline bg-white/[.025] px-3 py-2 text-xs text-muted hover:text-white"><Settings size={15}/> System settings</Link>}
        <div className="flex items-center justify-between px-2"><div className="flex items-center gap-2 text-[10px] uppercase tracking-[.16em] text-muted"><span className={`h-1.5 w-1.5 rounded-full ${mode === "offline" ? "bg-amber-400" : "bg-mint shadow-[0_0_8px_#83ffd1]"}`}/>{!collapsed && mode}</div>
          <button aria-label="Collapse sidebar" onClick={() => setCollapsed(!collapsed)} className="rounded-lg p-2 text-muted hover:bg-white/5 hover:text-white">{collapsed ? <Menu size={16}/> : <ChevronLeft size={16}/>}</button>
        </div>
      </div>
    </motion.aside>
    <motion.main animate={{ marginLeft: collapsed ? 76 : 244 }} className="relative min-h-screen w-full">{children}</motion.main>
  </div>;
}
