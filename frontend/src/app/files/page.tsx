"use client";

import { motion } from "framer-motion";
import { FileText, Image as ImageIcon, Loader2, UploadCloud } from "lucide-react";
import { DragEvent, useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { StoredFile } from "@/types";

export default function FilesPage() {
  const [files, setFiles] = useState<StoredFile[]>([]); const [uploading, setUploading] = useState(false); const [error, setError] = useState(""); const input = useRef<HTMLInputElement>(null);
  const load = () => api.files().then(setFiles); useEffect(() => { void load(); }, []);
  const ingest = async (list: FileList | File[]) => { setUploading(true); setError(""); try { for (const file of Array.from(list)) await api.upload(file); await load(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Upload failed"); } finally { setUploading(false); } };
  const drop = (event: DragEvent) => { event.preventDefault(); ingest(event.dataTransfer.files); };
  return <><PageHeader eyebrow="Local library" title="Files" description="Documents stay on this device; only retrieved excerpts may be sent to the model."/>
    <section className="p-8"><button onDragOver={event => event.preventDefault()} onDrop={drop} onClick={() => input.current?.click()} className="group grid w-full place-items-center rounded-2xl border border-dashed border-cyan/20 bg-cyan/[.025] py-12 transition hover:border-cyan/50 hover:bg-cyan/[.045]"><input ref={input} hidden multiple type="file" accept=".pdf,.txt,.md,.docx,image/*" onChange={event => event.target.files && ingest(event.target.files)}/>{uploading ? <Loader2 className="animate-spin text-cyan"/> : <UploadCloud className="text-cyan"/>}<div className="mt-3 text-sm text-white">{uploading ? "Extracting and indexing…" : "Drop files here or browse"}</div><div className="mt-1 text-xs text-muted">PDF, DOCX, TXT, Markdown, PNG, JPG, WEBP</div></button>
      {error && <div className="mt-4 rounded-xl border border-red-400/20 bg-red-400/5 p-3 text-sm text-red-200">{error}</div>}
      <div className="mt-8 grid gap-3">{files.map(file => <motion.article initial={{opacity:0}} animate={{opacity:1}} key={file.id} className="glass flex items-center gap-4 rounded-2xl p-4"><div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan/5 text-cyan">{file.mime_type.startsWith("image") ? <ImageIcon size={20}/> : <FileText size={20}/>}</div><div className="min-w-0 flex-1"><div className="truncate text-sm text-white">{file.filename}</div><div className="mt-1 text-[11px] text-muted">{file.page_count ? `${file.page_count} pages · ` : ""}{file.chunk_count} searchable chunks · {(file.size_bytes / 1024).toFixed(1)} KB</div></div><span className={`rounded-full px-2 py-1 text-[9px] uppercase tracking-widest ${file.status === "ready" ? "bg-mint/10 text-mint" : "bg-red-400/10 text-red-200"}`}>{file.status}</span></motion.article>)}</div>
      {!files.length && !uploading && <div className="py-16 text-center text-sm text-muted">Your local library is empty.</div>}
    </section>
  </>;
}
