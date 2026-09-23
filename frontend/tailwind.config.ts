import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#05090d",
        panel: "#0b141b",
        cyan: "#68e8ff",
        mint: "#83ffd1",
        muted: "#7d929f"
      },
      boxShadow: { glow: "0 0 50px rgba(104,232,255,.16)" },
      fontFamily: { sans: ["Inter", "Segoe UI", "sans-serif"], mono: ["JetBrains Mono", "Consolas", "monospace"] }
    }
  },
  plugins: []
} satisfies Config;

