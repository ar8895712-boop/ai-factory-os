/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Background tokens
        bg: {
          base:    '#000000',
          page:    '#131209',
          card:    '#181818',
          raised:  '#1F1F1F',
        },
        // Border tokens
        border: {
          subtle:  '#272727',
          default: '#313131',
        },
        // Status tokens
        status: {
          healthy:  '#4ade80',
          warning:  '#fbbf24',
          critical: '#f87171',
          info:     '#60a5fa',
        },
        // Text tokens
        text: {
          primary:   '#FFFFFF',
          secondary: '#9B9B9B',
          muted:     '#6B6B6B',
        },
      },
      transitionTimingFunction: {
        factory: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      transitionDuration: {
        300: '300ms',
        500: '500ms',
        600: '600ms',
        800: '800ms',
      },
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(32px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 600ms cubic-bezier(0.22,1,0.36,1) both',
      },
      maxWidth: {
        hero: '680px',
      },
    },
  },
  plugins: [],
}
