/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        lexi: {
          blue: "#2563eb",
          navy: "#111827",
        },
      },
    },
  },
  plugins: [],
};
