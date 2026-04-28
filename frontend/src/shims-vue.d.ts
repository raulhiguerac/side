/* eslint-disable */
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@vueform/vueform/locales/en';
declare module '@vueform/vueform/locales/*';
