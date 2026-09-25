import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <header className="relative flex items-end justify-between gap-6 border-b hairline px-8 py-7"><div className="absolute bottom-0 left-8 h-px w-24 bg-gradient-to-r from-cyan to-transparent"/><div><div className="flex items-center gap-2 text-[9px] uppercase tracking-[.3em] text-cyan"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan shadow-[0_0_10px_#68e8ff]"/>{eyebrow}</div><h1 className="mt-2 text-2xl font-light tracking-wide text-white">{title}</h1><p className="mt-1 text-sm text-muted">{description}</p></div>{action}</header>;
}
