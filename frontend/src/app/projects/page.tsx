"use client";

import { Plus } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";

type Project = { id: string; name: string; description: string; color: string; created_at: string };
export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]); const [name, setName] = useState(""); const [description, setDescription] = useState("");
  const load = () => api.projects().then(setProjects); useEffect(() => { void load(); }, []);
  const create = async (event: FormEvent) => { event.preventDefault(); if (!name.trim()) return; await api.createProject(name, description); setName(""); setDescription(""); load(); };
  return <><PageHeader eyebrow="Focused work" title="Projects" description="Keep chats, files, decisions, and tasks in context."/><div className="grid gap-5 p-8 lg:grid-cols-[360px_1fr]"><form onSubmit={create} className="glass h-fit rounded-2xl p-5"><h2 className="text-sm text-white">New project</h2><input value={name} onChange={e => setName(e.target.value)} placeholder="Project name" className="focus-ring mt-4 w-full rounded-xl border hairline bg-black/20 p-3 text-sm"/><textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="What is this project about?" rows={4} className="focus-ring mt-3 w-full resize-none rounded-xl border hairline bg-black/20 p-3 text-sm"/><button className="mt-3 flex items-center gap-2 rounded-xl bg-cyan px-4 py-2 text-sm text-void"><Plus size={15}/> Create</button></form><div className="grid gap-4 md:grid-cols-2">{projects.map(project => <article key={project.id} className="glass rounded-2xl p-5"><span className="mb-4 block h-1.5 w-8 rounded-full" style={{background:project.color}}/><h2>{project.name}</h2><p className="mt-2 text-sm text-muted">{project.description || "No description yet."}</p><div className="mt-5 text-[10px] uppercase tracking-widest text-muted">Created {new Date(project.created_at).toLocaleDateString()}</div></article>)}</div></div></>;
}
