"use client";

import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, ChevronLeft, Clock3, Files, FolderKanban, Home, Menu, MessageSquare, Network, Search, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { api } from "@/lib/api";

const navigation = [
  ["Home", "/", Home], ["Chat", "/chat", MessageSquare], ["Memory", "/memory", BrainCircuit],
  ["Files", "/files", Files], ["Knowledge Graph", "/graph", Network], ["Timeline", "/timeline", Clock3],
  ["Projects", "/projects", FolderKanban], ["Settings", "/settings", Settings],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mode, setMode] = useState("checking");
  useEffect(() => { api.health().then((health) => setMode(health.mode)).catch(() => setMode("offline")); }, []);
  if (path.startsWith("/quick") || path.startsWith("/capture")) return <main className="min-h-screen">{children}</main>;
  return <div className="flex min-h-screen">
    <motion.aside animate={{ width: collapsed ? 76 : 236 }} className="glass fixed inset-y-0 left-0 z-30 flex flex-col border-y-0 border-l-0">
      <div className="flex h-20 items-center gap-3 px-5">
        <div className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full border border-cyan/40 bg-cyan/5 text-cyan shadow-glow"><BrainCircuit size={19}/></div>
        <AnimatePresence>{!collapsed && <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="overflow-hidden whitespace-nowrap">
          <div className="text-sm font-semibold tracking-[.2em]">SECOND BRAIN</div><div className="text-[10px] uppercase tracking-[.2em] text-muted">Local intelligence</div>
        </motion.div>}</AnimatePresence>
      </div>
      <nav className="mt-3 flex-1 space-y-1 px-3">
        {navigation.map(([label, href, Icon]) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return <Link key={href} href={href} title={collapsed ? label : undefined} className={`group flex h-11 items-center gap-3 rounded-xl px-3 text-sm transition ${active ? "bg-cyan/10 text-cyan" : "text-muted hover:bg-white/[.04] hover:text-white"}`}>
            <Icon size={18} className="shrink-0"/>{!collapsed && <span className="whitespace-nowrap">{label}</span>}
            {active && <motion.span layoutId="nav" className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_12px_#68e8ff]"/>}
          </Link>;
        })}
      </nav>
      <div className="space-y-3 p-3">
        {!collapsed && <button className="flex w-full items-center gap-2 rounded-xl border hairline bg-white/[.025] px-3 py-2 text-xs text-muted hover:text-white"><Search size={15}/> <kbd className="ml-auto rounded border hairline px-1.5 py-0.5 text-[10px]">Ctrl Space</kbd></button>}
        <div className="flex items-center justify-between px-2"><div className="flex items-center gap-2 text-[10px] uppercase tracking-[.16em] text-muted"><span className={`h-1.5 w-1.5 rounded-full ${mode === "offline" ? "bg-amber-400" : "bg-mint shadow-[0_0_8px_#83ffd1]"}`}/>{!collapsed && mode}</div>
          <button aria-label="Collapse sidebar" onClick={() => setCollapsed(!collapsed)} className="rounded-lg p-2 text-muted hover:bg-white/5 hover:text-white">{collapsed ? <Menu size={16}/> : <ChevronLeft size={16}/>}</button>
        </div>
      </div>
    </motion.aside>
    <motion.main animate={{ marginLeft: collapsed ? 76 : 236 }} className="min-h-screen w-full">{children}</motion.main>
  </div>;
}
