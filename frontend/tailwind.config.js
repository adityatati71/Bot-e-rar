/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
      },
      colors: {
        navy: {
          50: '#eff2ff',
          100: '#dce3ff',
          200: '#b9c5ff',
          300: '#8a9fff',
          400: '#5a73ff',
          500: '#3554e8',
          600: '#2440c8',
          700: '#1d33a3',
          800: '#1a2d80',
          900: '#141f55',
          950: '#0d1438',
        },
        teal: {
          50: '#effcfb',
          100: '#d1f7f3',
          200: '#a4eee8',
          300: '#6de0d8',
          400: '#3ecbc2',
          500: '#22afa7',
          600: '#188d87',
          700: '#16716d',
          800: '#165a57',
          900: '#174a48',
        },
      },
      fontSize: {
        'xs': '0.6875rem',
        'sm': '0.75rem',
        'base': '0.8125rem',
        'md': '0.875rem',
        'lg': '1rem',
        'xl': '1.125rem',
        '2xl': '1.375rem',
        '3xl': '1.75rem',
      },
    },
  },
  plugins: [],
}
