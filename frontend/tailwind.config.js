/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b0d10",
        surface: "#101318",
        elevated: "#14171c",
        border: "#23272e",
        muted: "#8b929e",
        foreground: "#e6e8eb",
        accent: {
          DEFAULT: "#4f7cff",
          foreground: "#ffffff",
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "Consolas", "monospace"],
      },
      borderRadius: {
        lg: "10px",
        md: "8px",
        sm: "6px",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
