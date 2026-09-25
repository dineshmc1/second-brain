"use client";

import { X } from "lucide-react";
import { useCallback, useEffect } from "react";

export function useClosePopup() {
  return useCallback(async () => {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().hide();
    } catch {
      window.close();
    }
  }, []);
}

export function PopupCloseButton() {
  const close = useClosePopup();
  useEffect(() => {
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") void close();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [close]);

  return <button type="button" onClick={() => void close()} className="rounded-lg p-2 text-muted hover:bg-white/5 hover:text-white" aria-label="Close window" title="Close (Esc)"><X size={16}/></button>;
}
