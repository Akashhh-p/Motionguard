/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        ink: "#1F2937",
        muted: "#6B7280",
        panel: "#FFFFFF",
        canvas: "#EFF2EC",
        surface: "#F7F8F4",
        brand: "#5E6B4F",
        violet: "#8A735A",
        teal: "#15803D",
        border: "#E5E7E1",
        navy: "#1F2937",
        charcoal: "#1F2937",
        success: "#15803D",
        warning: "#B45309",
        danger: "#DC2626"
      },
      boxShadow: {
        premium: "0 8px 24px rgba(31, 41, 55, 0.06)",
        glow: "0 18px 46px rgba(94, 107, 79, 0.16)",
        mist: "0 1px 1px rgba(31, 41, 55, 0.03), 0 8px 24px rgba(31, 41, 55, 0.06)"
      }
    }
  },
  plugins: []
};
