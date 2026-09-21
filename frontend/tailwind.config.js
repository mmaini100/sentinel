/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F8FAFC',
        surface: '#FFFFFF',
        surfaceHover: '#F1F5F9',
        border: '#E2E8F0',
        text: {
          primary: '#0F172A',
          secondary: '#334155',
          muted: '#64748B',
        },
        status: {
          healthy: '#10B981',   // Emerald
          low: '#3B82F6',       // Blue
          medium: '#F59E0B',    // Amber
          high: '#F97316',      // Orange
          critical: '#EF4444',  // Red
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
