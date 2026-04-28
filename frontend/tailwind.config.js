/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/**/*.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./vueform.config.js",
    "./node_modules/@vueform/vueform/themes/tailwind/**/*.vue",
    "./node_modules/@vueform/vueform/themes/tailwind/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#22C55E", // Botones, estados activos
          "primary-light": "#DCFCE7", // Fondos seleccionados, disabled
          dark: "#0b2f2a", // Panel izquierdo
          text: "#2F3E3A", // Texto principal
          muted: "#6B7280", // Subtítulos
          placeholder: "#9CA3AF", // Placeholders
          bg: "#F7F9F8", // Fondo página
          border: "#D1D5DB", // Bordes inputs
          divider: "#E5E7EB", // Líneas, steps inactivos
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [require("@vueform/vueform/tailwind")],
};
