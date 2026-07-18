/* eslint-disable */
declare module '*.svg' {
  const src: string
  export default src
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@vueform/vueform/locales/en';
declare module '@vueform/vueform/locales/*';
declare module '*.css';
declare module 'leaflet.markercluster';
