import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <header className="flex items-end justify-between gap-6 border-b hairline px-8 py-7"><div><div className="text-[10px] uppercase tracking-[.24em] text-cyan">{eyebrow}</div><h1 className="mt-2 text-2xl font-light text-white">{title}</h1><p className="mt-1 text-sm text-muted">{description}</p></div>{action}</header>;
}

