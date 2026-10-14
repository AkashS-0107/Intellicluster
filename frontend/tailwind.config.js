/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: '#F5F7FB',
        card: '#FFFFFF',
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F8FAFC',
          raised: '#F1F5F9',
          overlay: '#E8EEFF',
        },
        border: {
          DEFAULT: '#DCE2ED',
          subtle: '#EAEFF7',
          strong: '#CBD5E1',
          active: '#244DE8',
        },
        ink: {
          DEFAULT: '#101828',
          secondary: '#475467',
          muted: '#667085',
          dim: '#98A2B3',
        },
        accent: {
          DEFAULT: '#244DE8',
          hover: '#1D40C7',
          active: '#16329C',
          subtle: '#E8EEFF',
          border: '#C7D7FE',
        },
        // Mapped design tokens for seamless editorial light theme compatibility
        cockpit: {
          bg: '#F5F7FB',
          surface: '#FFFFFF',
          raised: '#F8FAFC',
          overlay: '#F1F5F9',
          border: '#DCE2ED',
          'border-subtle': '#EAEFF7',
          'border-active': '#244DE8',
          text: '#101828',
          'text-muted': '#475467',
          'text-dim': '#667085',
          cyan: '#244DE8',
          'cyan-glow': 'rgba(36, 77, 232, 0.14)',
          success: '#027A48',
          'success-bg': '#ECFDF3',
          warning: '#B54708',
          'warning-bg': '#FFFAEB',
          critical: '#B42318',
          'critical-bg': '#FEF3F2',
        },
      },
      fontFamily: {
        sans: ['Geist', 'Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"Geist Mono"', '"JetBrains Mono"', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'panel': '0 1px 3px 0 rgba(16, 24, 40, 0.05), 0 1px 2px 0 rgba(16, 24, 40, 0.03)',
        'card': '0 1px 3px 0 rgba(16, 24, 40, 0.05), 0 1px 2px 0 rgba(16, 24, 40, 0.03)',
        'card-hover': '0 4px 12px 0 rgba(16, 24, 40, 0.08), 0 2px 4px 0 rgba(16, 24, 40, 0.03)',
        'cyan-glow': '0 0 14px 0 rgba(36, 77, 232, 0.16)',
        'accent-glow': '0 0 14px 0 rgba(36, 77, 232, 0.16)',
      },
    },
  },
  plugins: [],
}

