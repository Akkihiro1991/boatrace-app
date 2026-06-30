/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a1628',
          800: '#0f1f3d',
          700: '#1a2f55',
          600: '#1e3a6e',
        },
        lane: {
          1: '#f8f8f8',
          2: '#1a1a1a',
          3: '#dc2626',
          4: '#2563eb',
          5: '#ca8a04',
          6: '#16a34a',
        }
      }
    }
  },
  plugins: [],
}
