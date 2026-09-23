"use client";

import { motion } from "framer-motion";

export function Orb({ state = "idle", size = 156 }: { state?: "idle" | "listening" | "thinking" | "speaking"; size?: number }) {
  const active = state !== "idle";
  return <div className="relative grid place-items-center" style={{ width: size, height: size }} aria-label={`Assistant ${state}`}>
    {[1, .78, .57].map((scale, index) => <motion.div key={scale} className="absolute rounded-full border border-cyan/20"
      style={{ width: `${scale * 100}%`, height: `${scale * 100}%` }}
      animate={{ rotate: index % 2 ? -360 : 360, scale: active ? [scale, scale * 1.08, scale] : scale }}
      transition={{ rotate: { duration: 14 - index * 3, repeat: Infinity, ease: "linear" }, scale: { duration: .8, repeat: Infinity } }}>
      <span className="absolute left-1/2 top-[-3px] h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_14px_#68e8ff]"/>
    </motion.div>)}
    <motion.div className="h-[44%] w-[44%] rounded-full bg-[radial-gradient(circle_at_38%_35%,#eaffff_0,#68e8ff_18%,#1789a3_48%,#07161d_72%)] shadow-[0_0_40px_rgba(104,232,255,.5),inset_0_0_20px_rgba(255,255,255,.35)]"
      animate={{ scale: state === "listening" || state === "speaking" ? [1, 1.16, .96, 1] : [1, 1.04, 1], filter: state === "thinking" ? ["hue-rotate(0deg)", "hue-rotate(60deg)", "hue-rotate(0deg)"] : "none" }}
      transition={{ duration: state === "idle" ? 3 : .7, repeat: Infinity, ease: "easeInOut" }}/>
    <div className="absolute inset-0 rounded-full bg-cyan/5 blur-2xl"/>
  </div>;
}

