/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12202B",
        slate: "#3D5468",
        mist: "#EEF2F4",
        brand: {
          DEFAULT: "#1E5F5A",
          dark: "#153F3C",
          light: "#4C8C86",
        },
        clay: "#C4622D",
        warn: "#C99A2E",
        danger: "#B23A3A",
        ok: "#2E7D5B",
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
