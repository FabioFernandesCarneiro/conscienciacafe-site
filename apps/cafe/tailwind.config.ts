import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Consciência Café brand colors (from brandbook)
        // Proporção: 60% branco, 30% preto, 10% laranja
        primary: '#000000',
        accent: {
          DEFAULT: '#FF4611',
          hover: '#E53E0F',
        },
        gray: {
          light: '#F5F5F5',
          mid: '#6B7280',
          dark: '#374151',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      spacing: {
        // Touch-friendly minimums
        'touch': '44px',
      },
      minHeight: {
        'touch': '44px',
      },
      minWidth: {
        'touch': '44px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};

export default config;
