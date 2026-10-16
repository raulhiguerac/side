---
title: Inputs compartidos y tokens de color semánticos del frontend
captured-from: conversation
captured-on: 2026-10-16
participants: [raul, claude]
---

## Context
Segundo paso del sistema de componentes tras los botones (#31). Había 4 estilos de input a mano y ~60 colores semánticos crudos; el verde de marca con texto blanco no pasaba contraste AA. PR #32. Lint y vue-tsc pasan; el build no se re-corrió para no volver a tumbar a ORS por memoria.

## Key conclusions
- **Decisión del autor: dos alturas de campo.** `md` (`h-10`) para admin, settings y formularios de propiedad; `lg` (`h-12`) para auth y las confirmaciones de cuenta. Un solo look: borde 1px, `rounded-xl`, anillo de foco visible, borde rojo con `invalid`.
- **Decisión del autor: verde accesible en botones.** Token `primary-strong` `#15803D` (~5:1 con blanco) para el fondo de los botones primarios, los links y el texto del chip elegido; `brand-primary` `#22C55E` (~2,3:1) queda para acentos, bordes y fondos claros.
- Componentes en `components/shared/form/`: `BaseInput`, `BaseSelect`, `BaseTextarea`, `PasswordInput`, `FormField`, más `fieldClasses.ts` con las clases comunes. Reemplazan 74 campos.
- `BaseInput` y `BaseTextarea` escriben el valor a mano, sin la directiva `v-model` adentro: sirven con `v-model` y con `:value` + `@input` (el formato de precio de los formularios de propiedad), porque el `value` que llega por fallthrough pisa al del componente. `BaseSelect` sí usa el `v-model` nativo, que reaplica el valor cuando las opciones llegan después.
- `BaseInput` con `type="number"` emite número con `looseToNumber` (`utils/number.ts`), la misma regla del `.number` de Vue: lo que no parsea se devuelve tal cual y `""` queda `""`. Los modificadores `.number`/`.trim` del `v-model` de componente los aplica Vue 3.5 solo.
- `PasswordInput` absorbe los 5 "mostrar contraseña" (login, registro, tres en seguridad); el icono conserva la semántica de antes (ojo abierto = se ve) y el botón es un `IconButton` con `aria-label`.
- `FormField` (label + campo + error o ayuda) se adoptó solo en el admin, donde los 31 labels eran idénticos. Auth, settings y propiedades tienen labels con estilo propio por área; unificarlos cambiaría su aspecto y queda como decisión aparte.
- Tokens nuevos en `brandColors.json`: `primary-strong`, `primary-strong-hover`, `danger`, `danger-hover`, `danger-light`, `danger-border`, `success`, `success-light`, `success-border`, `warning`, `warning-light`, `warning-border`. 123 clases `red/green/yellow/orange/amber` crudas pasaron a tokens en 36 archivos; quedan crudas a propósito las paletas categóricas (puntos de rango de isócronas en `useReachablePois`, puntos de estado en `bulkJobStatus`/`propertyStatus`, sombras del indicador de pasos).
- Los checkbox de "capital" (localidad) y "soportado" (país) eran invisibles desde #29: la base de formularios del plugin de Vueform pone `appearance: none` a `[type="checkbox"]`. Llevan `appearance-auto`.
- Error propio detectado en navegador: al envolver labels en `FormField`, los labels interpolados (`{{ field.label }}`) se copiaron literal; se corrigieron a `:label`.

## Open questions
- ¿Unificar los labels de auth, settings y propiedades en `FormField` (cambia su aspecto)?
- ¿Variante de botón para fondo oscuro, para migrar los CTAs del hero del home?

## Next steps
- Probar en navegador lo no cubierto: login y registro, filtros del feed, inputs del AVM, perfil en settings, formularios de moderación y promoción.
