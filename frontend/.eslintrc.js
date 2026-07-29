module.exports = {
  root: true,
  env: {
    node: true,
    "vue/setup-compiler-macros": true,
  },
  extends: [
    "plugin:vue/vue3-essential",
    "eslint:recommended",
    "@vue/typescript/recommended",
    "plugin:prettier/recommended",
  ],
  parserOptions: {
    ecmaVersion: 2020,
  },
  rules: {
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    // Redundante con vue-tsc, que ya reporta identificadores no definidos y sí
    // entiende el type-space de TS. `no-undef` no lo ve, así que marca falsos
    // positivos en los parámetros de tipo de `<script setup generic="T">` y en
    // macros nuevos como `defineSlots`. Es la recomendación de typescript-eslint
    // para proyectos TS.
    "no-undef": "off",
  },
  globals: {
    google: "readonly",
    defineModel: "readonly",
  },
};
