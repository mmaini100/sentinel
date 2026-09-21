/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0E14',
        surface: '#151A23',
        surfaceHover: '#1E2532',
        border: '#2A3241',
        text: {
          primary: '#E2E8F0',
          secondary: '#94A3B8',
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
