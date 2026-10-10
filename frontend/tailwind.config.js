const plugin = require("tailwindcss/plugin");

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
        brand: require("./src/theme/brandColors.json"),
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [
    require("@vueform/vueform/tailwind"),
    // vueform redefine `disabled:` solo para descendientes; se suma el `:disabled` estándar.
    plugin(({ addVariant }) => {
      addVariant("disabled", ["&:disabled", "&[disabled]", "[disabled] &"]);
    }),
  ],
};
